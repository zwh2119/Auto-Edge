#!/bin/bash

# Function: Display help information
show_help() {
cat << EOF
Usage: ${0##*/} [--files [generator,distributor,controller,monitor,scheduler,car-detection...]] [--tag TAG] [--repo REPO] [--no-cache] [--help]

--files        Specify the images to build, separated by commas. Options include:
               generator
               distributor
               controller
               monitor
               scheduler
               car-detection
               Default is to select all.
--tag          Specify the version tag for the Docker images. Default is "v1.0.0".
--repo         Specify the repository for the Docker images. Default is "onecheck".
--no-cache     Build the Docker images without using cache.
--help         Display this help message and exit.
EOF
}

# Default Dockerfiles and their platforms
declare -A DOCKERFILES=(
    [generator]="templates/dockerfile/generator.Dockerfile"
    [distributor]="distributor/Dockerfile"
    [controller]="templates/dockerfile/controller.Dockerfile"
    [monitor]="monitor/Dockerfile"
    [scheduler]="scheduler/Dockerfile"
    [car-detection]="templates/dockerfile/car_detection.Dockerfile"
)

# Corresponding platforms
declare -A PLATFORMS=(
    [generator]="linux/arm64"
    [distributor]="linux/amd64"
    [controller]="linux/arm64,linux/amd64"
    [monitor]="linux/arm64,linux/amd64"
    [scheduler]="linux/amd64"
    [car-detection]="linux/amd64,linux/arm64"
)

# Initialize variables
SELECTED_FILES=""
TAG="v2.0.0"  # Default tag
REPO="onecheck"  # Default repository
NO_CACHE=false  # Default is to use cache

# Parse command line arguments
while :; do
    case $1 in
        --help)
            show_help    # Display help information
            exit 0
            ;;
        --files)
            if [ "$2" ]; then
                SELECTED_FILES=$2
                shift
            else
                echo 'ERROR: "--files" requires a non-empty option argument.'
                exit 1
            fi
            ;;
        --tag)
            if [ "$2" ]; then
                TAG=$2
                shift
            else
                echo 'ERROR: "--tag" requires a non-empty option argument.'
                exit 1
            fi
            ;;
        --repo)
            if [ "$2" ]; then
                REPO=$2
                shift
            else
                echo 'ERROR: "--repo" requires a non-empty option argument.'
                exit 1
            fi
            ;;
        --no-cache)
            NO_CACHE=true
            ;;
        --)              # End of options
            shift
            break
            ;;
        *)               # Default case
            break
    esac
    shift
done

build_image() {
    local image=$1
    local platform=$2
    local dockerfile=$3
    local cache_option=$4  # --no-cache or empty
    local image_tag="${REPO}/${image}:${TAG}"
    local context_dir="."

    echo "Building image: $image_tag on platform: $platform using Dockerfile: $dockerfile with no-cache: $NO_CACHE"

    if [ -z "$cache_option" ]; then
        docker buildx build --platform "$platform" --build-arg GO_LDFLAGS="" -t "$image_tag" -f "$dockerfile" "$context_dir" --push
    else
        docker buildx build  --platform "$platform" --build-arg GO_LDFLAGS="" -t "$image_tag" -f "$dockerfile" "$context_dir" "$cache_option" --push
    fi
}

build_image_special() {
    local image=$1
    local platform=$2
    local dockerfile=$3
    local cache_option=$4  # --no-cache or empty
    local temp_tag="${REPO}/${image}:${TAG}-${platform##*/}"  # Temporary tag for the build
    local context_dir="."

    echo "Building image: $temp_tag on platform: $platform using Dockerfile: $dockerfile with no-cache: $NO_CACHE"

    if [ -z "$cache_option" ]; then
        docker  buildx build --platform="$platform"  -t "$temp_tag" -f "$dockerfile" "$context_dir" --push
#        docker push "$temp_tag"
    else
        docker  buildx build  --platform="$platform"  -t "$temp_tag" -f "$dockerfile" "$context_dir" "$cache_option" --push
#        docker push "$temp_tag"

    fi
}

create_and_push_manifest() {
    local image=$1
    local tag=$2
    local repo=$3
    local manifest_tag="${repo}/${image}:${tag}"

    echo "Creating and pushing manifest for: $manifest_tag"

    docker manifest create "$manifest_tag" \
        "${repo}/${image}:${tag}-amd64" \
        "${repo}/${image}:${tag}-arm64"

    docker manifest annotate "$manifest_tag" "${repo}/${image}:${tag}-amd64" --os linux --arch amd64
    docker manifest annotate "$manifest_tag" "${repo}/${image}:${tag}-arm64" --os linux --arch arm64

    docker manifest push "$manifest_tag"
}

# Determine if --no-cache should be used
CACHE_OPTION=""
if [ "$NO_CACHE" = true ] ; then
    CACHE_OPTION="--no-cache"
fi

# specified platforms
if [ -n "$SELECTED_FILES" ]; then
    IFS=',' read -ra ADDR <<< "$SELECTED_FILES"
    for image in "${ADDR[@]}"; do
        if [[ -n "${DOCKERFILES[$image]}" && -n "${PLATFORMS[$image]}" ]]; then
            build_image "$image" "${PLATFORMS[$image]}" "${DOCKERFILES[$image]}" "$CACHE_OPTION"

        else
            echo "Unknown image or platform not specified: $image"
        fi
    done
else
    echo "No images specified, building all default images."
    for image in "${!DOCKERFILES[@]}"; do
            build_image "$image" "${PLATFORMS[$image]}" "${DOCKERFILES[$image]}" "$CACHE_OPTION"
    done
fi

