#!/bin/bash

# 显示帮助信息
function show_help() {
    echo "Usage: $0 <input_file> <specific_address>"
    echo
    echo "This script continuously streams the input video file to an RTSP server."
    echo
    echo "Arguments:"
    echo "  <input_file>:     Path to the input video file."
    echo "  <specific_address>: Specific address to append to 'rtsp://127.0.0.1/'."
    echo
    echo "Example:"
    echo "  $0 /path/to/your/input/file.mp4 your_specific_address"
    exit 1
}

# 检查是否提供了足够的参数
if [ "$#" -ne 2 ]; then
    show_help
fi

rtsp_url="rtsp://127.0.0.1/$2"

while true; do
    ffmpeg -i "$1" -rtsp_transport tcp -vcodec h264 -f rtsp "$rtsp_url"
done

