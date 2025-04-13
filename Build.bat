@echo off

cl /EHsc /I "imgui" main.cpp imgui\imgui.cpp imgui\imgui_draw.cpp imgui\imgui_widgets.cpp imgui\imgui_tables.cpp imgui\imgui_demo.cpp imgui\imgui_impl_win32.cpp imgui\imgui_impl_dx11.cpp /link d3d11.lib dxgi.lib d3dcompiler.lib user32.lib gdi32.lib