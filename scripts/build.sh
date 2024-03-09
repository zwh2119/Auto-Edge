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
               license-plate-detection
               imu-trajectory-sensing
               Default is to select all.
--tag          Specify the version tag for the Docker images. Default is "v1.0.0".
--repo         Specify the repository for the Docker images. Default is "onecheck".
--no-cache     Build the Docker images without using cache.
--help         Display this help message and exit.
EOF
}

# Default Dockerfiles and their platforms
declare -A DOCKERFILES=(
    [generator]="generator/Dockerfile"
    [distributor]="distributor/Dockerfile"
    [controller]="controller/Dockerfile"
    [monitor]="monitor/Dockerfile"
    [scheduler]="scheduler/Dockerfile"
    [car-detection]="car_detection/Dockerfile"
    [license-plate-detection]="license_plate_detection/Dockerfile"
    [imu-trajectory-sensing]="imu_trajectory_sensing/Dockerfile"
    [audio-sampling]="audio_sampling/Dockerfile"
    [audio-classification]="audio_classification/Dockerfile"
    [edge-eye-stage1]="edge_eye/stage1/Dockerfile"
    [edge-eye-stage2]="edge_eye/stage2/Dockerfile"
    [edge-eye-stage3]="edge_eye/stage3/Dockerfile"
)

# Corresponding platforms
declare -A PLATFORMS=(
    [generator]="linux/arm64"
    [distributor]="linux/amd64"
    [controller]="linux/arm64,linux/amd64"
    [monitor]="linux/arm64,linux/amd64"
    [scheduler]="linux/amd64"
    [car-detection]="linux/amd64,linux/arm64"
    [license-plate-detection]="linux/amd64,linux/arm64"
    [imu-trajectory-sensing]="linux/amd64,linux/arm64"
    [audio-sampling]="linux/amd64,linux/arm64"
    [audio-classification]="linux/amd64,linux/arm64"
    [edge-eye-stage1]="linux/amd64,linux/arm64"
    [edge-eye-stage2]="linux/amd64,linux/arm64"
    [edge-eye-stage3]="linux/amd64,linux/arm64"
)

# Images requiring special treatment, their platforms, and Dockerfiles
declare -A SPECIAL_BUILD=(
    [car-detection]="linux/amd64:car_detection/Dockerfile,linux/arm64:car_detection/arm64.Dockerfile"
    [audio-classification]="linux/amd64:audio_classification/Dockerfile,linux/arm64:audio_classification/arm64.Dockerfile"
)

# Initialize variables
SELECTED_FILES=""
TAG="v1.0.0"  # Default tag
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
    local tag_suffix=$4  # May be empty
    local cache_option=$5  # --no-cache or empty
    local image_tag="${REPO}/${image}:${tag_suffix}${TAG}"
    local context_dir=$(dirname "$dockerfile")  # Get the directory of the Dockerfile

    echo "Building image: $image_tag on platform: $platform using Dockerfile: $dockerfile with no-cache: $NO_CACHE"

    if [ -z "$cache_option" ]; then
        docker buildx build --platform "$platform" --build-arg GO_LDFLAGS="" -t "$image_tag" -f "$dockerfile" "$context_dir" --push
    else
        docker buildx build  --platform "$platform" --build-arg GO_LDFLAGS="" -t "$image_tag" -f "$dockerfile" "$context_dir" "$cache_option" --push
    fi
}

# Determine if --no-cache should be used
CACHE_OPTION=""
if [ "$NO_CACHE" = true ] ; then
    CACHE_OPTION="--no-cache"
fi

# Compile Docker images based on --files argument and specified platforms
if [ -n "$SELECTED_FILES" ]; then
    IFS=',' read -ra ADDR <<< "$SELECTED_FILES"
    for image in "${ADDR[@]}"; do
        if [[ -n "${DOCKERFILES[$image]}" && -n "${PLATFORMS[$image]}" ]]; then
            # Check if it's a specially treated image
            if [[ -n "${SPECIAL_BUILD[$image]}" ]]; then
                IFS=',' read -ra SPECIAL_PLATFORMS <<< "${SPECIAL_BUILD[$image]}"
                for entry in "${SPECIAL_PLATFORMS[@]}"; do
                    IFS=':' read -ra DETAILS <<< "$entry"
                    platform="${DETAILS[0]}"
                    dockerfile="${DETAILS[1]}"
                    tag_suffix=""
                    [[ $platform == "linux/arm64" ]] && tag_suffix="arm64-"
                    build_image "$image" "$platform" "$dockerfile" "$tag_suffix" "$CACHE_OPTION"
                done
            else
                build_image "$image" "${PLATFORMS[$image]}" "${DOCKERFILES[$image]}" "" "$CACHE_OPTION"
            fi
        else
            echo "Unknown image or platform not specified: $image"
        fi
    done
else
    echo "No images specified, building all default images."
    for image in "${!DOCKERFILES[@]}"; do
        if [[ -n "${SPECIAL_BUILD[$image]}" ]]; then
            IFS=',' read -ra SPECIAL_PLATFORMS <<< "${SPECIAL_BUILD[$image]}"
            for entry in "${SPECIAL_PLATFORMS[@]}"; do
                IFS=':' read -ra DETAILS <<< "$entry"
                platform="${DETAILS[0]}"
                dockerfile="${DETAILS[1]}"
                tag_suffix=""
                [[ $platform == "linux/arm64" ]] && tag_suffix="arm64-"
                build_image "$image" "$platform" "$dockerfile" "$tag_suffix" "$CACHE_OPTION"
            done
        else
            build_image "$image" "${PLATFORMS[$image]}" "${DOCKERFILES[$image]}" "" "$CACHE_OPTION"
        fi
    done
fi
