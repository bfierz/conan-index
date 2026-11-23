// VCL configuration
#include <vcl/config/global.h>

// Include the relevant parts from the library
#include <vcl/components/entitymanager.h>
#include <vcl/compute/context.h>
#include <vcl/core/simd/vectorscalar.h>
#include <vcl/geometry/distancePoint3Triangle3.h>
#include <vcl/math/math.h>
#include <vcl/math/polardecomposition.h>

// Graphics backends (vcl::graphics), which define their VCL_*_SUPPORT macro
#ifdef VCL_OPENGL_SUPPORT
#	include <vcl/graphics/opengl/context.h>
#	include <vcl/graphics/opengl/gl.h>
#endif

// C++ standard library
#include <cmath>
#include <cstdio>
#include <type_traits>

int main()
{
	using Vcl::float4;
	using Vcl::float8;
	using Vcl::float16;
	using Vcl::Mathematics::equal;

	// SIMD (vcl::core): sqrt on every vector width
	const float4 vec1{ 0.0f, 6.10116f, 11.6117f, 11.8436f };
	const float8 vec2{ 0.0f, 6.10116f, 11.6117f, 11.8436f, 0.0f, 6.10116f, 11.6117f, 11.8436f };
	const float16 vec3{ 0.0f, 6.10116f, 11.6117f, 11.8436f, 0.0f, 6.10116f, 11.6117f, 11.8436f,
						0.0f, 6.10116f, 11.6117f, 11.8436f, 0.0f, 6.10116f, 11.6117f, 11.8436f };
	const float4 ref1{ 0.0f, 2.4700526f, 3.4075945f, 3.4414532f };
	const float8 ref2{ 0.0f, 2.4700526f, 3.4075945f, 3.4414532f, 0.0f, 2.4700526f, 3.4075945f, 3.4414532f };
	const float16 ref3{ 0.0f, 2.4700526f, 3.4075945f, 3.4414532f, 0.0f, 2.4700526f, 3.4075945f, 3.4414532f,
						0.0f, 2.4700526f, 3.4075945f, 3.4414532f, 0.0f, 2.4700526f, 3.4075945f, 3.4414532f };
	if (!all(equal(ref1, sqrt(vec1), float4(1e-5f))) || !all(equal(ref2, sqrt(vec2), float8(1e-5f))) || !all(equal(ref3, sqrt(vec3), float16(1e-5f))))
	{
		std::printf("SIMD sqrt failed\n");
		return 1;
	}

	// Math (vcl::math): the rotation of a uniform scaling is the identity
	Eigen::Matrix<float4, 3, 3> A = Eigen::Matrix<float4, 3, 3>::Identity() * float4(2.0f);
	Eigen::Matrix<float4, 3, 3> R;
	Vcl::Mathematics::PolarDecomposition(A, R, nullptr);
	for (int i = 0; i < 3; i++)
		for (int j = 0; j < 3; j++)
			if (!all(equal(R(i, j), float4(i == j ? 1.0f : 0.0f), float4(1e-5f))))
			{
				std::printf("Polar decomposition failed\n");
				return 1;
			}

	// Geometry (vcl::geometry): distance of a point above a triangle
	const Vcl::Geometry::Triangle<float, 3> triangle{ Eigen::Vector3f{ 0, 0, 0 }, Eigen::Vector3f{ 1, 0, 0 }, Eigen::Vector3f{ 0, 1, 0 } };
	const float d = Vcl::Geometry::distance(triangle, Eigen::Vector3f{ 0.25f, 0.25f, 1 });
	if (std::fabs(d - 1.0f) > 1e-5f)
	{
		std::printf("Point-triangle distance failed\n");
		return 1;
	}

	// Components (vcl::components)
	Vcl::Components::EntityManager entities;
	entities.destroy(entities.create());

#ifdef VCL_OPENGL_SUPPORT
	// OpenGL (vcl::graphics): the format tables need no GL context
	if (Vcl::Graphics::OpenGL::GL::toRenderType(Vcl::Graphics::SurfaceFormat::R8G8B8A8_UNORM).internalFormat() != GL_RGBA8)
	{
		std::printf("OpenGL render type failed\n");
		return 1;
	}
	std::printf("vcl: OpenGL works\n");
#endif
#ifdef VCL_EGL_SUPPORT
	// EGL (vcl::graphics): the EGL context constructor exists. Referencing the context code
	// links it, and with it EGL, without creating a context.
	static_assert(std::is_constructible_v<Vcl::Graphics::OpenGL::Context, EGLDisplay, EGLSurface>, "EGL context constructor");
	const char* (*volatile profile_type)() = &Vcl::Graphics::OpenGL::Context::profileType;
	if (profile_type == nullptr)
		return 1;
	std::printf("vcl: EGL context links\n");
#endif

	std::printf("vcl: SIMD, math, geometry and components work\n");
	return 0;
}
