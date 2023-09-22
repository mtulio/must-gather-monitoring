
REPO ?= git@github.com:openshift/must-gather
REPO_VER ?= master
DEST_REPO ?= ./build

CMD_CNT ?= podman
IMAGE_NAME ?= quay.io/mrbraga/must-gather
IMAGE_VERSION ?= $(shell git rev-parse --short HEAD)-$(shell date +%Y%m%d%H%M%S)

.PHONY: all
all: clone build-image push-image

.PHONY: update
update:
	test -d $(DEST_REPO) && ( \
		cd $(DEST_REPO); \
		git pull; )

.PHONY: clone
clone:
	test -d $(DEST_REPO) || mkdir -p $(DEST_REPO)
	test -d $(DEST_REPO) && \
		git clone --recursive \
			$(REPO) -b $(REPO_VER) $(DEST_REPO)

.PHONY: build-image
build-image:
	cp -v gather-monitoring-metrics $(DEST_REPO)/collection-scripts/
	cp -v Containerfile $(DEST_REPO)/
	@echo "\n>> Build image: $(IMAGE_NAME):$(IMAGE_VERSION)"
	cd $(DEST_REPO); \
		$(CMD_CNT) build \
			--authfile $(HOME)/.openshift/pull-secret-latest.json \
			-f Containerfile -t $(IMAGE_NAME):$(IMAGE_VERSION) .
	$(CMD_CNT) tag $(IMAGE_NAME):$(IMAGE_VERSION) $(IMAGE_NAME):latest
	$(CMD_CNT) push $(IMAGE_NAME):latest
	$(CMD_CNT) push $(IMAGE_NAME):$(IMAGE_VERSION)
	echo "export VERSION=$(IMAGE_NAME):$(IMAGE_VERSION)"

.PHONY: push-image
push-image:
	@echo "\n>> Pushing image to registry: $(IMAGE_NAME):$(IMAGE_VERSION)|latest"
	$(CMD_CNT) push $(IMAGE_NAME):latest

# make image IMAGE_VERSION=$(git rev-parse --short HEAD)-${RANDOM}
.PHONY: image
image: clone build-image push-image
