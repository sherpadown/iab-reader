docker.build:
	docker build --no-cache -t iab-reader:latest .

docker.run:
	docker run -it --rm iab-reader:latest --help

docker.run.tests:
	docker run -v "$(PWD)/tests/assets:/assets" -it --rm iab-reader:latest -f /assets/silence.iab
