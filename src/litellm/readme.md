## 이미지 빌드
docker build -t litellm-proxy .

# 컨테이너 run
docker run -d \
  --env-file ./.env \
  -p 4000:4000 \
  --name my-litellm-container \
  litellm-proxy
