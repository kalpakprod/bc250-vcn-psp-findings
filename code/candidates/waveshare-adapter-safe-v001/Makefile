.PHONY: all build test flash clean configure

BUILD ?= build
# Required: make BUILD_DATE=2026-10-03T00:00:00Z build
BUILD_DATE ?=

all: build

configure:
	cmake -S . -B $(BUILD) -G Ninja -DCMAKE_BUILD_TYPE=Release -DWAVESHARE_RP2350B_PLUS_W_BUILD=ON -DENABLE_SERIAL=ON -DENABLE_WOL=OFF -DPICO_SDK_PATH=$(CURDIR)/lib/pico-sdk -DBUILD_DATE="$(BUILD_DATE)"

build: configure
	cmake --build $(BUILD) --target unified

test: build
	python3 tests/test_unified.py

flash: build
	@echo "Put Waveshare in BOOTSEL (hold BOOT + press RESET), then run:"
	@echo "  cp $(BUILD)/unified.uf2 /run/media/$$USER/RP2350/"

clean:
	rm -rf $(BUILD)
