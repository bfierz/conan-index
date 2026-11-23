// Built only when the tested vcl package has with_opengl=True
#include <vcl/config/global.h>
#ifndef VCL_OPENGL_SUPPORT
#	error "vcl::graphics does not define VCL_OPENGL_SUPPORT"
#endif
#if defined TEST_EGL && !defined VCL_EGL_SUPPORT
#	error "vcl::graphics does not define VCL_EGL_SUPPORT"
#endif

#include <vcl/graphics/opengl/context.h>
#include <vcl/graphics/opengl/gl.h>

// C++ standard library
#include <cstdio>
#include <type_traits>

// Needs no GL context: the format tables are static. Linking gl.cpp pulls in OpenGL and GLEW.
bool testOpenGL()
{
	using namespace Vcl::Graphics;

	if (OpenGL::GL::toRenderType(SurfaceFormat::R8G8B8A8_UNORM).internalFormat() != GL_RGBA8)
	{
		std::printf("OpenGL render type failed\n");
		return false;
	}

#ifdef TEST_EGL
	// The EGL context constructor exists. Referencing the context code links it, and with it
	// EGL, without creating a context.
	static_assert(std::is_constructible_v<OpenGL::Context, EGLDisplay, EGLSurface>, "EGL context constructor");
	const char* (*volatile profile_type)() = &OpenGL::Context::profileType;
	if (profile_type == nullptr)
	{
		std::printf("EGL context failed to link\n");
		return false;
	}
#endif
	return true;
}
