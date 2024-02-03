import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { StereoscopicEffects } from 'threejs-StereoscopicEffects';

let scene, lights, camera, renderer, controls, stereofx;
let cube_types = [
	new THREE.MeshLambertMaterial({ color: 0x333333, transparent: true, opacity: 0.8 }),
	new THREE.MeshLambertMaterial({ color: 0x0066d4, transparent: true, opacity: 0.8 }),
	new THREE.MeshLambertMaterial({ color: 0xffcc00, transparent: true, opacity: 0.2 }),
	new THREE.MeshLambertMaterial({ color: 0xcccccc, transparent: true, opacity: 0.2 }),
	new THREE.MeshLambertMaterial({ color: 0xf40000, transparent: true, opacity: 0.1 }),
	new THREE.MeshLambertMaterial({ color: 0x00f400, transparent: true, opacity: 0.1 }),
	new THREE.MeshLambertMaterial({ color: 0x0000f4, transparent: true, opacity: 0.1 }),
	new THREE.MeshLambertMaterial({ color: 0xf400f4, transparent: true, opacity: 0.1 }),
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
	const lines = new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({ color: cube_types[1].color }));
	scene.add(lines);
}

function addCube(i, t, px, py, pz, mx, my, mz) {
	const p = coord_l2xyz(i);
	if (p.x == 0) mx = 0;
	if (p.y == 0) my = 0;
	if (p.z == 0) mz = 0;
	if (p.x == gridSize.x - 1) px = 0;
	if (p.y == gridSize.y - 1) py = 0;
	if (p.z == gridSize.z - 1) pz = 0;
	const sx = (px+mx)*CUBESZ/2;
	const sy = (py+my)*CUBESZ/2;
	const sz = (pz+mz)*CUBESZ/2;
	const geometry = new THREE.BoxGeometry(sx, sy, sz);
	const material = cube_types[t];
	const cube = new THREE.Mesh(geometry, material);
	cube.position.x = p.wx + (sx - mx * CUBESZ)/2;
	cube.position.y = p.wy + (sy - my * CUBESZ)/2;
	cube.position.z = p.wz + (sz - mz * CUBESZ)/2;
	cubes.push(cube);
	scene.add(cube);

	const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geometry), new THREE.LineBasicMaterial({color: material.color, linewidth: 3}));
	edges.computeLineDistances();
	edges.position.add(cube.position);
	scene.add(edges);
}

function addPath(pts) {
	const material = new THREE.LineBasicMaterial({ color: 0xffffff });
	const geometry = new THREE.BufferGeometry().setFromPoints(pts);
	const line = new THREE.Line(geometry, material);
	scene.add(line);
}

const b64_digits = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

function b64_itoa(number) {
	let str = '';
	let nb = Math.floor(number);
	while (nb > 0) {
		str = b64_digits.charAt(nb % 64) + str;
		nb = Math.floor(nb / 64);
	}
	return str;
}

function b64_atoi(str) {
	let nb = 0;
	for (const c of str.split('')) nb = (nb * 64) + b64_digits.indexOf(c);
	return nb;
}

function block_to_b64(bt, px, py, pz, mx, my, mz) {
	const nb = (px << 0) +
		   (mx << 2) +
		   (py << 4) +
		   (my << 6) +
		   (pz << 8) +
		   (mz << 10) +
		   (bt << 12);
	return b64_itoa(nb);
}

function parseLog(txt) {
	// It is assumed that the log is valid

	// Grid size
	{
		const map = txt.match(/MAP[^\n]+\n/)[0]?.split(/\s+/);
		gridSize = { x: parseInt(map[1]), y: parseInt(map[2]), z: parseInt(map[3]) };
	}

	// Grid on
	{
		const gridon = txt.match(/GRID ON\n/);
		addGrid(gridon != null);
	}

	// Decode grid
	{
		const ratios = [0, 1/3, 2/3, 1]
		const grid = txt.match(/MAP.*\n([\s\S]*)ENDMAP/m)[1]?.replaceAll(/[^A-Za-z0-9+\/]+/g, '')?.match(/.{3}/g) || [];
		for (const [i, v] of grid.entries()) {
			if (v == 'AAA') continue;
			const nb = b64_atoi(v);
			const px = ratios[(nb & (3 << 0)) >> 0];
			const mx = ratios[(nb & (3 << 2)) >> 2];
			const py = ratios[(nb & (3 << 4)) >> 4];
			const my = ratios[(nb & (3 << 6)) >> 6];
			const pz = ratios[(nb & (3 << 8)) >> 8];
			const mz = ratios[(nb & (3 << 10)) >> 10];
			const bt = (nb & (7 << 12)) >> 12;
			addCube(i, bt, px, py, pz, mx, my, mz);
		}
	}

	// Path
	{
		const path = txt.match(/(START[\s\S]*END.*\n)/m)[1]?.match(/.*\n/g) || [];
		const points = [];
		let px = 0, py = 0, pz = 0;
		let vx = 0, vy = 0, vz = 0;
		for (const p of path) {
			const d = p.split(/\s/);
			if (d[0] == "START") {
				px = parseInt(d[1]);
				py = parseInt(d[2]);
				pz = parseInt(d[3]);
				const q = coord_l2xyz(coord_xyz2l(px, py, pz));
				points.push(new THREE.Vector3(q.wx, q.wy, q.wz));
			} else if (d[0] == "VEC") {
				vx += parseInt(d[1]);
				vy += parseInt(d[2]);
				vz += parseInt(d[3]);
				px += vx;
				py += vy;
				pz += vz;
				const q = coord_l2xyz(coord_xyz2l(px, py, pz));
				points.push(new THREE.Vector3(q.wx, q.wy, q.wz));
			} else if (d[0] == "END") {
				addPath(points);
			}
		}
	}
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

	parseLog(`
GRID OFF
MAP 10 8 5
BMz AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA BP/ AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA

AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA CP/ C/9 AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA

AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA EVV FVV GVV HVV AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA D// AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA

AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AVV AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA

AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
ENDMAP
START 2 1 2
VEC 0 1 0
VEC 1 0 0
VEC 0 -1 0
VEC 1 0 0
VEC -1 1 1
VEC -1 -1 -1
VEC -1 0 0
VEC -1 0 0
END OK
`);
}

function render(time) {
	requestAnimationFrame(render);
	controls.update();
	stereofx.render(scene, camera);
}

init();
render(0);
