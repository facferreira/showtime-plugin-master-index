all:
	mkdir -p output
	./indexer.py output plugins/*

clean:
	rm -rf output
	rm *~

upload:
	rsync -rv output/ showtime.lonelycoder.com:showtime.lonelycoder.com/plugins

updateall:
	for a in plugins/* ; do (cd $$a ; echo $$a; git checkout master && git pull --rebase); done
