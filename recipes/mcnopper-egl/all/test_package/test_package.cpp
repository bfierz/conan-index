#include <EGL/egl.h>

#include <cstdio>

int main()
{
	// Only needs the library to link and EGL 1.5's API binding to succeed; no GPU context is created
	if (eglBindAPI(EGL_OPENGL_API) != EGL_TRUE)
		return 1;

	std::printf("EGL API bound, current API 0x%x\n", static_cast<unsigned>(eglQueryAPI()));
	return 0;
}
