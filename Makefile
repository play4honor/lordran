HUB ?= public.ecr.aws/o4s5x0l8
VERSION ?= latest

ecr-login:
	aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(HUB)

build-solaire: bot/Dockerfile
	docker build -t $(HUB)/solaire:$(VERSION) -f bot/Dockerfile .

build-quelaag: backend/Dockerfile
	docker build -t $(HUB)/quelaag:$(VERSION) -f backend/Dockerfile .

push-solaire: ecr-login
	docker push $(HUB)/solaire:$(VERSION)

push-quelaag: ecr-login
	docker push $(HUB)/quelaag:$(VERSION)

pull-solaire: ecr-login
	docker pull $(HUB)/solaire:$(VERSION)

pull-quelaag: ecr-login
	docker pull $(HUB)/quelaag:$(VERSION)

run:
	docker run -d \
	--env-file ./SECRETS/solaire.env \
	$(HUB)/solaire:$(VERSION)
	docker run -d \
	--env-file ./SECRETS/quelaag.env \
	$(HUB)/quelaag:$(VERSION)
