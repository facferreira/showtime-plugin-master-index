all:
	mkdir -p output
	./plugin_indexer.py output plugins/*

clean:
	rm -rf output
	rm *~
