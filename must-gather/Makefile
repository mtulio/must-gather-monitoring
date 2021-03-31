
REPO ?= git@github.com:mtulio/must-gather
REPO_VER ?= fix/gather-monitoring
DEST_REPO ?= ./.build

CMD_CNT ?= sudo podman
IMAGE_NAME ?= quay.io/rhn_support_mrbraga/must-gather
IMAGE_VERSION ?= $(shell git rev-parse --short HEAD)
IMAGE_NAME_GH ?= docker.pkg.github.com/mtulio/must-gather-monitoring/must-gather-monitoring

.PHONY: all
all: clone build-image push-image

.PHONY: update
update:
	test -d $(DEST_REPO) && ( \
		cd $(DEST_REPO); \
		git pull; )

.PHONY: clone
clone:
	test -d $(DEST_REPO) || \
		git clone --recursive \
			$(REPO) -b $(REPO_VER) $(DEST_REPO)

.PHONY: build-image
build-image:
	@echo "\n>> Build image: $(IMAGE_NAME):$(IMAGE_VERSION)"
	cd $(DEST_REPO); \
		$(CMD_CNT) build -t $(IMAGE_NAME):$(IMAGE_VERSION) .
	$(CMD_CNT) tag $(IMAGE_NAME):$(IMAGE_VERSION) $(IMAGE_NAME):latest
	$(CMD_CNT) tag $(IMAGE_NAME):$(IMAGE_VERSION) $(IMAGE_NAME_GH):$(IMAGE_VERSION)
	$(CMD_CNT) tag $(IMAGE_NAME):latest $(IMAGE_NAME_GH):latest

.PHONY: push-image
push-image:
	@echo "\n>> Pushing image to registry: $(IMAGE_NAME):$(IMAGE_VERSION)"
	$(CMD_CNT) push $(IMAGE_NAME):$(IMAGE_VERSION)
	$(CMD_CNT) push $(IMAGE_NAME):latest
	$(CMD_CNT) push $(IMAGE_NAME_GH):$(IMAGE_VERSION)
	$(CMD_CNT) push $(IMAGE_NAME_GH):latest

# make image IMAGE_VERSION=$(git rev-parse --short HEAD)-${RANDOM}
.PHONY: image
image: clone build-image push-image
