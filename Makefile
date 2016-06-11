.PHONY: all
all: video.webm

video.webm: video.ppm

video.ppm: git gource.conf
	gource --load-config gource.conf -r 30 -o video.ppm git

git: create_mfnf_git.py
	rm -rfv git
	python3 create_mfnf_git.py
