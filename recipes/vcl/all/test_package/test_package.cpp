// VCL configuration
#include <vcl/config/global.h>

// The package's instruction set (vcl/config/config.h) must be enabled in this compiler, which
// only happens through the flags the vcl targets carry. MSVC defines no macros for SSE.
#if defined(VCL_VECTORIZE_AVX512) && !(defined(__AVX512F__) && defined(__AVX512VL__) && defined(__AVX512DQ__))
#	error "vcl is built for AVX 512, but the consumer does not get the AVX 512 flags"
#elif defined(VCL_VECTORIZE_AVX2) && !defined(__AVX2__)
#	error "vcl is built for AVX 2, but the consumer does not get the AVX 2 flag"
#elif defined(VCL_VECTORIZE_AVX) && !defined(__AVX__)
#	error "vcl is built for AVX, but the consumer does not get the AVX flag"
#elif !defined(_MSC_VER) && defined(VCL_VECTORIZE_SSE4_2) && !defined(__SSE4_2__)
#	error "vcl is built for SSE 4.2, but the consumer does not get the SSE 4.2 flag"
#elif !defined(_MSC_VER) && defined(VCL_VECTORIZE_SSE4_1) && !defined(__SSE4_1__)
#	error "vcl is built for SSE 4.1, but the consumer does not get the SSE 4.1 flag"
#elif !defined(_MSC_VER) && defined(VCL_VECTORIZE_SSSE3) && !defined(__SSSE3__)
#	error "vcl is built for SSSE 3, but the consumer does not get the SSSE 3 flag"
#elif !defined(_MSC_VER) && defined(VCL_VECTORIZE_SSE3) && !defined(__SSE3__)
#	error "vcl is built for SSE 3, but the consumer does not get the SSE 3 flag"
#endif

// The instruction set named like the recipe's `vectorize` option
#if defined(VCL_VECTORIZE_AVX512)
#	define VCL_TEST_VECTORIZE "avx512"
#elif defined(VCL_VECTORIZE_AVX2)
#	define VCL_TEST_VECTORIZE "avx2"
#elif defined(VCL_VECTORIZE_AVX)
#	define VCL_TEST_VECTORIZE "avx"
#elif defined(VCL_VECTORIZE_SSE4_2)
#	define VCL_TEST_VECTORIZE "sse4.2"
#elif defined(VCL_VECTORIZE_SSE4_1)
#	define VCL_TEST_VECTORIZE "sse4.1"
#elif defined(VCL_VECTORIZE_SSSE3)
#	define VCL_TEST_VECTORIZE "ssse3"
#elif defined(VCL_VECTORIZE_SSE3)
#	define VCL_TEST_VECTORIZE "sse3"
#elif defined(VCL_VECTORIZE_SSE2)
#	define VCL_TEST_VECTORIZE "sse2"
#elif defined(VCL_VECTORIZE_NEON)
#	define VCL_TEST_VECTORIZE "neon"
#else
#	define VCL_TEST_VECTORIZE "generic"
#endif

// Include the relevant parts from the library
#include <vcl/components/entitymanager.h>
#include <vcl/compute/context.h>
#include <vcl/core/simd/vectorscalar.h>
#include <vcl/geometry/distancePoint3Triangle3.h>
#include <vcl/graphics/matrixfactory.h>
#include <vcl/math/math.h>
#include <vcl/math/polardecomposition.h>

// C++ standard library
#include <cmath>
#include <cstdio>

// Graphics backends, one test_<backend>.cpp each. They return false on failure.
#ifdef TEST_OPENGL
bool testOpenGL();
#endif
#ifdef TEST_D3D12
bool testD3D12();
#endif

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

	// Graphics (vcl::graphics): a Direct3D projection maps the near plane to depth 0
	const Vcl::Graphics::Direct3D::MatrixFactory factory;
	const Eigen::Vector4f p = factory.createPerspectiveFov(1.0f, 10.0f, 1.0f, 1.0f) * Eigen::Vector4f{ 0, 0, -1, 1 };
	if (std::fabs(p.z() / p.w()) > 1e-5f)
	{
		std::printf("Perspective projection failed\n");
		return 1;
	}

#ifdef TEST_OPENGL
	if (!testOpenGL())
		return 1;
#endif
#ifdef TEST_D3D12
	if (!testD3D12())
		return 1;
#endif

	std::printf("vcl: instruction set %s\n", VCL_TEST_VECTORIZE);
	std::printf("vcl: SIMD, math, geometry, components and graphics work\n");
	return 0;
}
