#include <ImFileDialog.h>

#include <cstdio>

int main()
{
	auto& dialog = ifd::FileDialog::Instance();
	dialog.CreateTexture = [](uint8_t*, int, int, char) -> void* { return nullptr; };
	dialog.DeleteTexture = [](void*) {};

	// Opening only records the request and reads the start directory; drawing needs an ImGui frame
	if (!dialog.Open("TestOpen", "Open a file", "All files (*.*){.*}", false, "."))
		return 1;
	dialog.Close();

	std::printf("ImFileDialog opened and closed a dialog\n");
	return 0;
}
