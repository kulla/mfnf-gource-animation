.PHONY: all
all: video.webm

video.webm: video.ppm
	ffmpeg -y -r 30 -f image2pipe -vcodec ppm -i video.ppm \
		-vcodec libvpx -b 10000K video.webm

video.ppm: git gource.conf mfnf.png
	gource --load-config gource.conf -r 30 -o video.ppm git

mfnf.png: mfnf.jpg
	convert $< -resize x250 $@

git: create_mfnf_git.py
	python3 create_mfnf_git.py

.PHONY: clean
clean:
	rm -rf git video.ppm video.webm mfnf.png
