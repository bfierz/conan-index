// Built only when the tested vcl package has with_webgpu=True
#include <vcl/config/global.h>
#ifndef VCL_WEBGPU_SUPPORT
#	error "vcl::graphics does not define VCL_WEBGPU_SUPPORT"
#endif

#include <vcl/graphics/webgpu/webgpu.h>

// C++ standard library
#include <cstdio>

// Needs no GPU: toWebGPUEnum() only maps the enum, and a WebGPU instance exists without an
// adapter. Creating it calls into Dawn's shared library (Emscripten's bindings in the browser).
bool testWebGPU()
{
	using Vcl::Graphics::SurfaceFormat;
	using Vcl::Graphics::WebGPU::toWebGPUEnum;

	if (toWebGPUEnum(SurfaceFormat::R32G32B32A32_FLOAT) != WGPUTextureFormat_RGBA32Float)
	{
		std::printf("WebGPU surface format conversion failed\n");
		return false;
	}

	WGPUInstance instance = wgpuCreateInstance(nullptr);
	if (!instance)
	{
		std::printf("WebGPU instance creation failed\n");
		return false;
	}
	wgpuInstanceRelease(instance);
	return true;
}
