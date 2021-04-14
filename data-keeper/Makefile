CMD_CNT ?= podman
IMAGE_NAME ?= quay.io/rhn_support_mrbraga/mgm-data-keeper
IMAGE_VERSION ?= $(shell git rev-parse --short HEAD)

build:
.PHONY: build
build:
	@echo "\n>> Build image: $(IMAGE_NAME):$(IMAGE_VERSION)"
	$(CMD_CNT) build -t $(IMAGE_NAME):$(IMAGE_VERSION) .
	$(CMD_CNT) tag $(IMAGE_NAME):$(IMAGE_VERSION) $(IMAGE_NAME):latest

.PHONY: push
push:
	@echo "\n>> Pushing image to registry: $(IMAGE_NAME):$(IMAGE_VERSION)"
	$(CMD_CNT) push $(IMAGE_NAME):$(IMAGE_VERSION)
	$(CMD_CNT) push $(IMAGE_NAME):latest
