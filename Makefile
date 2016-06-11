.PHONY: all
all: video.webm

video.webm: video.ppm
	ffmpeg -y -r 30 -f image2pipe -vcodec ppm -i video.ppm \
		-vcodec libvpx -b 10000K video.webm

video.ppm: git gource.conf
	gource --load-config gource.conf -r 30 -o video.ppm git

git: create_mfnf_git.py
	rm -rfv git
	python3 create_mfnf_git.py
