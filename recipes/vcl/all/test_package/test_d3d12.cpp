// Built only when the tested vcl package has with_d3d12=True
#include <vcl/config/global.h>
#ifndef VCL_D3D12_SUPPORT
#	error "vcl::graphics does not define VCL_D3D12_SUPPORT"
#endif

#include <vcl/graphics/d3d12/d3d.h>
#include <vcl/graphics/d3d12/device.h>

// C++ standard library
#include <cstdio>
#include <vector>

// Needs no GPU: both functions only inspect their arguments. Linking device.cpp pulls in
// d3d12, dxgi and dxguid.
bool testD3D12()
{
	using namespace Vcl::Graphics::D3D12;

	const std::vector<AdapterInfo> adapters{ { "WARP", false, 0 }, { "GPU", true, 1024 } };
	if (selectAdapter(adapters, DeviceType::Hardware) != 1 || selectAdapter({}, DeviceType::Hardware) != -1)
	{
		std::printf("D3D12 adapter selection failed\n");
		return false;
	}
	if (!isDepthFormat(DXGI_FORMAT_D32_FLOAT) || isDepthFormat(DXGI_FORMAT_R8G8B8A8_UNORM))
	{
		std::printf("D3D12 depth format check failed\n");
		return false;
	}
	return true;
}
