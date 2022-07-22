HUB ?= public.ecr.aws/o4s5x0l8
VERSION ?= latest
IMAGE ?= solaire

.PHONY: ecr-login build push pull run

ecr-login:
	aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(HUB)

build: Dockerfile
	docker build -t $(HUB)/$(IMAGE):$(VERSION) -f Dockerfile .

push: ecr-login
	docker push $(HUB)/$(IMAGE):$(VERSION)

pull: ecr-login
	docker pull $(HUB)/$(IMAGE):$(VERSION)

run:
	docker run -d \
	--env-file ../SECRETS/solaire.env \
	$(HUB)/$(IMAGE):$(VERSION)