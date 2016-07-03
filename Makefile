.PHONY: all
all: video.webm

video.webm: video.ppm audio.wav
	ffmpeg -y -r 30 -f image2pipe -vcodec ppm -i video.ppm \
		-codec:v libvpx -quality best -cpu-used 0 -b:v 1M \
		-qmin 10 -qmax 42 -maxrate 2M -bufsize 2M -threads 4 \
		-an -pass 1 -f webm /dev/null
	ffmpeg -y -r 30 -f image2pipe -vcodec ppm -i video.ppm -i audio.wav \
		-codec:v libvpx -quality best -cpu-used 0 -b:v 1M -qmin 10 \
		-qmax 42 -maxrate 2M -bufsize 2M -threads 4 \
		-codec:a libvorbis -b:a 164k -pass 2 -f webm video.webm

video.ppm: git gource.conf mfnf.png
	gource --load-config gource.conf -r 30 -o video.ppm -1920x1080 git

mfnf.png: mfnf.jpg
	convert $< -resize x250 $@

git: create_mfnf_git.py
	python3 create_mfnf_git.py

.PHONY: clean
clean:
	rm -rf git video.ppm video.webm mfnf.png
