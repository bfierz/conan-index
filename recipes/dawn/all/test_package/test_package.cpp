#include <dawn/native/DawnNative.h>

#include <memory>

int main()
{
	auto instance = std::make_unique<dawn::native::Instance>();
	instance->GetDeviceCountForTesting();
	return 0;
}
