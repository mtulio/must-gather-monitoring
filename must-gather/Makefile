
REPO ?= git@github.com:mtulio/must-gather
REPO_VER ?= fix/monitoring-review0
DEST_REPO ?= ./.build

CMD_CNT ?= sudo podman
IMAGE_NAME ?= quay.io/rhn_support_mrbraga/must-gather
IMAGE_VERSION ?= $(shell git rev-parse --short HEAD)

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

.PHONY: push-image
push-image:
	@echo "\n>> Pushing image to registry: $(IMAGE_NAME):$(IMAGE_VERSION)"
	cd $(DEST_REPO); \
		$(CMD_CNT) push $(IMAGE_NAME):$(IMAGE_VERSION)

# make image IMAGE_VERSION=$(git rev-parse --short HEAD)-${RANDOM}
.PHONY: image
image: clone build-image push-image
