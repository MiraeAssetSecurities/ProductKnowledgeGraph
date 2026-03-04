#!/usr/bin/env bash
set -euo pipefail

log() { echo "[$(date '+%F %T')] $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

need_cmd() { command -v "$1" >/dev/null 2>&1 || die "필수 명령이 없습니다: $1"; }

need_cmd findmnt
need_cmd lsblk

ROOT_SRC="$(findmnt -n -o SOURCE /)"   # 예: /dev/nvme0n1p1, /dev/xvda1, /dev/mapper/...
FSTYPE="$(findmnt -n -o FSTYPE /)"

log "Root source: ${ROOT_SRC}"
log "Filesystem: ${FSTYPE}"

# LVM/mapper는 별도 절차
if [[ "${ROOT_SRC}" == /dev/mapper/* ]]; then
  die "루트가 LVM(/dev/mapper/*)입니다. pvresize/lvextend가 필요합니다."
fi

# growpart 준비
if ! command -v growpart >/dev/null 2>&1; then
  log "growpart가 없어 설치합니다 (cloud-guest-utils / cloud-utils-growpart)."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y cloud-guest-utils
  elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y cloud-utils-growpart
  else
    die "패키지 매니저(apt/yum)를 찾지 못했습니다. growpart를 수동 설치해주세요."
  fi
fi

DISK=""
PART_NUM=""

# NVMe: /dev/nvme0n1p1 형태
if [[ "${ROOT_SRC}" =~ ^/dev/nvme[0-9]+n[0-9]+p[0-9]+$ ]]; then
  DISK="${ROOT_SRC%p*}"             # /dev/nvme0n1
  PART_NUM="${ROOT_SRC##*p}"        # 1
# 일반: /dev/xvda1, /dev/sda1 형태
elif [[ "${ROOT_SRC}" =~ ^/dev/[a-z]+[a-z0-9]*[0-9]+$ ]]; then
  PART_NUM="$(echo "${ROOT_SRC}" | grep -oE '[0-9]+$')"
  DISK="$(echo "${ROOT_SRC}" | sed -E 's/[0-9]+$//')"
else
  # 혹시 모를 케이스: lsblk로 fallback
  log "디바이스명 파싱이 애매해서 lsblk로 재시도합니다."
  PKNAME="$(lsblk -no PKNAME "${ROOT_SRC}" 2>/dev/null || true)"
  PART_NUM="$(lsblk -no PARTNUM "${ROOT_SRC}" 2>/dev/null || true)"
  [[ -n "${PKNAME}" && -n "${PART_NUM}" ]] || die "디스크/파티션 정보를 찾지 못했습니다: ${ROOT_SRC}"
  DISK="/dev/${PKNAME}"
fi

[[ -b "${DISK}" ]] || die "부모 디스크가 블록디바이스가 아닙니다: ${DISK}"
[[ "${PART_NUM}" =~ ^[0-9]+$ ]] || die "파티션 번호가 이상합니다: ${PART_NUM}"

log "Parent disk: ${DISK}, partition: ${PART_NUM}"

log "커널에 변경 반영(partprobe)..."
sudo partprobe "${DISK}" || true

log "파티션 확장: growpart ${DISK} ${PART_NUM}"
sudo growpart "${DISK}" "${PART_NUM}"

log "파일시스템 확장..."
case "${FSTYPE}" in
  ext4|ext3|ext2)
    sudo resize2fs "${ROOT_SRC}"
    ;;
  xfs)
    sudo xfs_growfs /
    ;;
  *)
    die "지원하지 않는 파일시스템: ${FSTYPE} (ext4/xfs만 지원)"
    ;;
esac

log "완료! 최종 확인:"
df -hT /
lsblk