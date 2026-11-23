// Built only when the tested vcl package has with_vulkan=True
#include <vcl/config/global.h>
#ifndef VCL_VULKAN_SUPPORT
#	error "vcl::graphics does not define VCL_VULKAN_SUPPORT"
#endif

#include <vcl/graphics/runtime/vulkan/resource/shader.h>

// C++ standard library
#include <cstdio>

// Needs no Vulkan device: convert() only maps the enum. Linking shader.cpp pulls in the
// Vulkan loader and spirv-cross.
bool testVulkan()
{
	using Vcl::Graphics::Runtime::ShaderType;
	using Vcl::Graphics::Runtime::Vulkan::Shader;

	if (Shader::convert(ShaderType::ComputeShader) != VK_SHADER_STAGE_COMPUTE_BIT)
	{
		std::printf("Vulkan shader stage conversion failed\n");
		return false;
	}
	return true;
}
