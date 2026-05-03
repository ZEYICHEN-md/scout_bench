#!/bin/bash
# 打包 social-media-analysis skill
# 用法: cd skills/ && bash social-media-analysis/package.sh

cd "$(dirname "$0")"
zip -r ../social-media-analysis.skill social-media-analysis/
echo "Packaged: ../social-media-analysis.skill"
