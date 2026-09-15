import os

def main():
    src = os.path.join('src', 'geolibre_frontend', 'geolibre_cesium_3d_viewer.html')
    with open(src, 'r', encoding='utf-8') as f:
        content = f.read()

    sub_content = content.replace('href="assets/', 'href="../assets/')
    sub_content = sub_content.replace('href="potree_viewer.html"', 'href="../potree_viewer.html"')
    sub_content = sub_content.replace('href="copc_3d_viewer.html"', 'href="../copc_3d_viewer.html"')
    sub_content = sub_content.replace('href="cesium_wireframe_tin.html"', 'href="../cesium_wireframe_tin.html"')
    sub_content = sub_content.replace('href="map.html"', 'href="../map.html"')
    sub_content = sub_content.replace('href="data_qa.html', 'href="../data_qa.html')

    targets = [
        os.path.join('src', 'geolibre_frontend', 'projects', 'geolibre_cesium_3d_viewer.html'),
        os.path.join('src', 'geolibre_frontend', 'tests', 'cesium_3d_test.html'),
        os.path.join('src', 'geolibre_frontend', 'tests', 'cesium_test.html'),
        os.path.join('tests', 'frontend', 'cesium_3d_test.html'),
        os.path.join('tests', 'frontend', 'cesium_test.html')
    ]

    for t in targets:
        os.makedirs(os.path.dirname(t), exist_ok=True)
        with open(t, 'w', encoding='utf-8') as f:
            f.write(sub_content)
        print(f"Synced {t}")

if __name__ == '__main__':
    main()
