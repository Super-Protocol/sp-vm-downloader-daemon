VERSION ?= 0.0.0

SHELL := /bin/bash

OUTPUT=build
SOURCE=app
MISC=misc

ARGS :=

APP_NAME=sp-vm-downloader-daemon_$(VERSION)-1_amd64
SOURCES=$(shell find $(SOURCE) -type f)
MISC_FILES=$(shell find $(MISC) -type f)

PROTO_DIR=$(SOURCE)/proto
PROTO_GEN_DIR=$(SOURCE)/modules/proto
PROTO_SRC=$(PROTO_DIR)/sp_vm_downloader.proto
PROTO_DST=$(PROTO_GEN_DIR)/sp_vm_downloader_pb2.py \
		  $(PROTO_GEN_DIR)/sp_vm_downloader_pb2_grpc.py

all: $(OUTPUT)/$(APP_NAME).deb

$(OUTPUT)/venv/bin/activate: $(SOURCE)/requirements.txt $(MISC_FILES) Makefile
	@echo -e "\tVENV\t$(OUTPUT)/venv"
	@mkdir -p $(OUTPUT)/venv
	@python3 -m venv $(OUTPUT)/venv
	@source $(OUTPUT)/venv/bin/activate && \
		python3 -m pip install -r \
		$(SOURCE)/requirements.txt && \
		python3 -m pip install -r \
		$(SOURCE)/lint_requirements.txt

$(PROTO_DST): $(PROTO_SRC) $(OUTPUT)/venv/bin/activate
	@echo -e "\tPROTO\t$<"
	@mkdir -p $(PROTO_GEN_DIR)
	@touch $(PROTO_GEN_DIR)/__init__.py
	@source $(OUTPUT)/venv/bin/activate && \
		python3 -m grpc_tools.protoc \
		-I $(PROTO_DIR) \
		--python_out=$(PROTO_GEN_DIR) \
		--grpc_python_out=$(PROTO_GEN_DIR) \
		$<
	@python3 misc/scripts/fix_proto_imports.py $(PROTO_GEN_DIR)

.PHONY: run
run: $(PROTO_DST)
	@source $(OUTPUT)/venv/bin/activate && \
		python3 $(SOURCE)/main.py $(ARGS)


$(OUTPUT)/$(APP_NAME).deb: $(SOURCES) $(PROTO_DST)
	mkdir -p $(OUTPUT)/$(APP_NAME)/DEBIAN
	mkdir -p $(OUTPUT)/$(APP_NAME)/usr/bin
	mkdir -p $(OUTPUT)/$(APP_NAME)/etc/systemd/system/
	mkdir -p $(OUTPUT)/$(APP_NAME)/usr/bin
	mkdir -p $(OUTPUT)/$(APP_NAME)/usr/bin/sp-vm-downloader-daemon/app
	cp -Lr $(SOURCE) $(OUTPUT)/$(APP_NAME)/usr/bin/sp-vm-downloader-daemon/app
	cp $(MISC)/sp-vm-downloader-daemon.service $(OUTPUT)/$(APP_NAME)/etc/systemd/system/sp-vm-downloader-daemon.service
	VERSION="${VERSION}" envsubst '$$VERSION' < $(MISC)/control > $(OUTPUT)/$(APP_NAME)/DEBIAN/control
	cp $(MISC)/postinst $(OUTPUT)/$(APP_NAME)/DEBIAN/
	cp $(MISC)/prerm $(OUTPUT)/$(APP_NAME)/DEBIAN/
	dpkg-deb --build --root-owner-group $(OUTPUT)/$(APP_NAME)

.PHONY: format
format: $(OUTPUT)/venv/bin/activate
	python3 -m isort --profile black --length-sort --reverse-sort \
		--multi-line 3 --skip-glob '*_pb2.py' --skip-glob '*_pb2_grpc.py' .
	python3 -m black --skip-string-normalization \
		--line-length=120 --extend-exclude '.*_pb2(_grpc)?\.py' .

.PHONY: lint
lint: $(OUTPUT)/venv/bin/activate
	python3 -m isort --profile black --length-sort --reverse-sort \
		--multi-line 3 --skip-glob '*_pb2.py' --skip-glob '*_pb2_grpc.py' --check --diff .
	python3 -m black --skip-string-normalization \
		--line-length=120 --extend-exclude '.*_pb2(_grpc)?\.py' --check --diff .

.PHONY: clean
clean:
	rm -rf $(OUTPUT)
