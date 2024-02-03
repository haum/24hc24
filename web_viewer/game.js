import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { StereoscopicEffects } from 'threejs-StereoscopicEffects';

let scene, lights, camera, renderer, controls, stereofx, ship;
let cube_types = [
	new THREE.MeshLambertMaterial({ color: 0xd40000 }),
	new THREE.MeshLambertMaterial({ color: 0xffcc00 }),
];
let cubes = [];
const CUBESZ = 0.1;

let gridSize = { x: 10, y: 10, z: 10 };

function coord_l2xyz(i) {
	const z = Math.floor(i / (gridSize.x * gridSize.y));
	i -= z * gridSize.x * gridSize.y;
	const y = Math.floor(i / gridSize.x);
	const x = i % gridSize.x
	return {
		x: x, y: y, z: z,
		wx: (x - gridSize.x/2) * CUBESZ,
		wy: (y - gridSize.y/2) * CUBESZ,
		wz: (z - gridSize.z/2) * CUBESZ,
	};
}

function coord_xyz2l(x, y, z) {
	return x + y * gridSize.x + z * gridSize.x * gridSize.y;
}

function addGrid(inside) {
	const n = gridSize.x * gridSize.y * gridSize.z;
	const geometry = new THREE.BufferGeometry();

	const positions = [];
	for (let i = 0; i < n; i++) {
		const p = coord_l2xyz(i);
		positions.push(p.wx, p.wy, p.wz);
	}
	geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
	const indexPairs = [];
	for (let i = 0; i < n; i++) {
		const p = coord_l2xyz(i);
		const px_minmax = p.x == 0 || p.x == gridSize.x-1;
		const py_minmax = p.y == 0 || p.y == gridSize.y-1;
		const pz_minmax = p.z == 0 || p.z == gridSize.z-1;
		if (p.x + 1 < gridSize.x && (inside || (py_minmax && pz_minmax))) {
			indexPairs.push(i);
			indexPairs.push(coord_xyz2l(p.x + 1, p.y, p.z));
		}
		if (p.y + 1 < gridSize.y && (inside || (pz_minmax && px_minmax))) {
			indexPairs.push(i);
			indexPairs.push(coord_xyz2l(p.x, p.y + 1, p.z));
		}
		if (p.z + 1 < gridSize.z && (inside || (px_minmax && py_minmax))) {
			indexPairs.push(i);
			indexPairs.push(coord_xyz2l(p.x, p.y, p.z + 1));
		}
	}
	geometry.setIndex(indexPairs);
	const lines = new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({ color: 0x88AA00}));
	scene.add(lines);
}

function addCube(i, t, px, py, pz, mx, my, mz) {
	const cube = new THREE.Mesh(new THREE.BoxGeometry(CUBESZ, CUBESZ, CUBESZ), cube_types[t]);
	const p = coord_l2xyz(i);
	cube.position.x = p.wx;
	cube.position.y = p.wy;
	cube.position.z = p.wz;
	cubes.push(cube);
	scene.add(cube);
}

function parseLog(txt) {
	// Fake
	gridSize = { x: 10, y: 8, z:5 };
	addGrid(false);
	addCube(0, 0, 1, 1, 1, 1, 1, 1);
	addCube(12, 0, 1, 1, 1, 1, 1, 1);
	addCube(112, 1, 1, 1, 1, 1, 1, 1);
	addCube(113, 1, 1, 1, 1, 1, 1, 1);
}

function init() {
	scene = new THREE.Scene();
	const defaultEffect = 20; // Anaglyph RC half-colors

	const loader = new THREE.TextureLoader();
	scene.background = loader.load('bg.webp');
	scene.background.colorSpace = THREE.SRGBColorSpace;

	lights = [];
	lights[0] = new THREE.AmbientLight({ intensity: 1 });
	lights[1] = new THREE.DirectionalLight( 0xffffff, 3 );
	lights[2] = new THREE.DirectionalLight( 0xffffff, 3 );
	lights[3] = new THREE.DirectionalLight( 0xffffff, 3 );
	lights[1].position.set(0, 200, 0);
	lights[2].position.set(100, 200, 100);
	lights[3].position.set(-100, -200, -100);
	scene.add(lights[0]);
	scene.add(lights[1]);
	scene.add(lights[2]);
	scene.add(lights[3]);

	camera = new THREE.PerspectiveCamera(24, window.innerWidth / window.innerHeight, 1/100, 100);
	camera.position.set(0, 3, 3);
	camera.lookAt(scene.position);

	renderer = new THREE.WebGLRenderer({ antialias: true, antialias: true });
	renderer.setPixelRatio(window.devicePixelRatio);
	stereofx = new StereoscopicEffects(renderer, defaultEffect);
	stereofx.setSize(window.innerWidth, window.innerHeight);
 
	controls = new OrbitControls(camera, renderer.domElement);
	controls.enableDamping = true;
	controls.dampingFactor = 0.05;
	controls.screenSpacePanning = false;
	controls.listenToKeyEvents(window);
	
	ship = new THREE.Mesh(new THREE.TetrahedronGeometry(0.05), new THREE.MeshLambertMaterial(0xffff00));
	scene.add(ship);

	const modes = StereoscopicEffects.effectsListForm();
	modes.value = defaultEffect;
	modes.style.position = 'absolute';
	modes.style.top = 0;
	modes.style.right = 0;
	modes.addEventListener('change', () => {
		stereofx.setEffect(modes.value);
	});
	document.body.appendChild(modes);

	window.addEventListener('resize', () => {
		camera.aspect = window.innerWidth / window.innerHeight;
		camera.updateProjectionMatrix();
		stereofx.setSize(window.innerWidth, window.innerHeight);
	});

	document.body.appendChild(renderer.domElement);

	parseLog('');
}

let ltime = 0;
function render(time) {
	const dt = (time - ltime) / 1000;
	ltime = time;

	requestAnimationFrame(render);

//	const speed = 0.5;
//	cube.rotation.x -= dt * speed * 2;
//	cube.rotation.y -= dt * speed;
//	cube.rotation.z -= dt * speed * 3;

	controls.update();
	stereofx.render(scene, camera);
}

init();
render(0);
