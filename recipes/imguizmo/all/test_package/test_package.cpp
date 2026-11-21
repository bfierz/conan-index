#include <imgui.h>
#include <ImGuizmo.h>

#include <cmath>
#include <cstdio>

int main()
{
	// Matrix helpers need no ImGui frame: decompose a translation matrix (column-major)
	const float matrix[16] = { 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 2, 3, 1 };
	float translation[3], rotation[3], scale[3];
	ImGuizmo::DecomposeMatrixToComponents(matrix, translation, rotation, scale);

	if (std::fabs(translation[0] - 1.0f) > 1e-5f || std::fabs(translation[1] - 2.0f) > 1e-5f || std::fabs(translation[2] - 3.0f) > 1e-5f)
		return 1;

	std::printf("ImGuizmo decomposed a matrix with imgui %s\n", IMGUI_VERSION);
	return 0;
}
