#include <dawn/native/DawnNative.h>

#include <memory>

int main()
{
	auto instance = std::make_unique<dawn_native::Instance>();
	instance->DiscoverDefaultAdapters();
	return 0;
}
