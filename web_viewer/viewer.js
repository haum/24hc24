import * as THREE from 'three';
import { TrackballControls } from 'three/addons/controls/TrackballControls.js';
import { StereoscopicEffects } from 'threejs-StereoscopicEffects';

let scene, background, lights, camera, renderer, controls, stereofx;
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
let dynobjs = [];
const CUBESZ = 0.1;

let gridSize = { x: 10, y: 10, z: 10 };
let path_line = null;

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

function rmDynobjs() {
	for (const obj of dynobjs) {
		scene.remove(obj);
	}
	dynobjs = [];
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
	dynobjs.push(lines);
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
	cube.renderOrder = 1;
	dynobjs.push(cube);
	scene.add(cube);

	const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geometry), new THREE.LineBasicMaterial({color: material.color}));
	edges.computeLineDistances();
	edges.position.add(cube.position);
	dynobjs.push(edges);
	scene.add(edges);
}

function addPath(pts, actions) {
	const sphere_geometry = new THREE.SphereGeometry(CUBESZ/20, 8, 8);
	const sphere_material = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.5 });
	for (const pt of pts.slice(0, -1)) {
		const sphere = new THREE.Mesh(sphere_geometry, sphere_material);
		sphere.position.add(pt);
		dynobjs.push(sphere);
		scene.add(sphere);
	}

	const material = new THREE.ShaderMaterial({
		uniforms: {
			"t": { value: 0.0 },
			"maxActions": { value: 1.0 }
		},
		vertexShader: `
			attribute float lineDistance;
			attribute float actionNb;
			varying float vLineDistance;
			varying float vActionNb;
			void main() {
				vLineDistance = lineDistance;
				vActionNb = actionNb;
				gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
			}
		`,
		fragmentShader: `
			uniform float t;
			uniform float maxActions;
			varying float vLineDistance;
			varying float vActionNb;

			void main() {
				vec4 color = vec4(vec3(0.5), 1.0);
				if (mod(vLineDistance - t/1500.0*0.02, 0.02) > 0.01)
					color = vec4(vec3(0.3), 1.0);

				float b = mod(t/1000.0, maxActions);
				float a = b - 0.8;
				if (a < vActionNb && vActionNb < b) {
					const vec3 chl = vec3(0.1, 1.0, 0.1);
					float p = (vActionNb - a) / (b-a);
					color.xyz += p*p*p*p * chl * 0.8;
				}

				gl_FragColor = color;
			}
		`
	});
	material.linewidth = 2;
	const geometry = new THREE.BufferGeometry().setFromPoints(pts);
	geometry.setAttribute('actionNb', new THREE.Float32BufferAttribute(actions, 1));
	const line = new THREE.Line(geometry, material);
	line.computeLineDistances();
	line.material.uniforms.maxActions.value = actions[actions.length-1];
	dynobjs.push(line);
	path_line = line;
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

export function block_to_b64(bt, px, py, pz, mx, my, mz) {
	const nb = ((px & 3) << 0) +
		   ((mx & 3) << 2) +
		   ((py & 3) << 4) +
		   ((my & 3) << 6) +
		   ((pz & 3) << 8) +
		   ((mz & 3) << 10) +
		   ((bt & 7) << 12);
	return ('AAA'+b64_itoa(nb)).substr(-3);
}

export function parseLog(buf) {
	const buf8 = new Uint8Array(buf);
	if (buf8[0] == 31 && buf8[1] == 139) { // Gzip
		const ds = new DecompressionStream("gzip");
		const writer = ds.writable.getWriter();
		writer.write(buf);
		writer.close();
		new Response(ds.readable).text().then(t => parseLogTxt(t));
	} else {
		const decoder = new TextDecoder();
		parseLogTxt(decoder.decode(buf));
	}
}

export function parseLogTxt(txt) {
	// It is assumed that the log is valid
	rmDynobjs();

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
		const actions = [];
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
				actions.push(0.0);
			} else if (d[0] == "ACC") {
				vx += parseInt(d[1]);
				vy += parseInt(d[2]);
				vz += parseInt(d[3]);
				px += vx;
				py += vy;
				pz += vz;
				const q = coord_l2xyz(coord_xyz2l(px, py, pz));
				points.push(new THREE.Vector3(q.wx, q.wy, q.wz));
				actions.push(actions.length * 1.0);
			} else if (d[0] == "END") {
				const l = parseFloat(d[2]);
				const origin = points[Math.floor(l)];
				const destination = points[Math.ceil(l)];
				const ndest = origin.clone().lerp(destination, l%1);
				points.splice(Math.ceil(l));
				points.push(ndest);
				actions.splice(Math.ceil(l));
				actions.push(l);
				addPath(points, actions);
			}
		}
	}
}

export function parseLogFetch(url) {
	fetch(url)
		.then(r => r.arrayBuffer())
		.then(b => parseLog(b));
}

export function init() {
	const defaultEffect = 20; // Anaglyph RC half-colors

	scene = new THREE.Scene();
	scene.background = new THREE.Color(0xAAAAAA);

	const loader = new THREE.TextureLoader();
	background = loader.load('bg.webp');
	background.colorSpace = THREE.SRGBColorSpace;

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
 
	controls = new TrackballControls(camera, renderer.domElement);
	controls.rotateSpeed = 1.0;
	controls.zoomSpeed = 1.0;
	controls.panSpeed = 0.1;
	controls.keys = ['CtrlLeft', 'AltLeft', 'ShiftLeft'];

	const modes = StereoscopicEffects.effectsListForm();
	modes.value = defaultEffect;
	modes.style.position = 'absolute';
	modes.style.top = 0;
	modes.style.right = 0;
	modes.addEventListener('change', () => {
		stereofx.setEffect(modes.value);
		if (modes.value > 18)
			scene.background = new THREE.Color(0xAAAAAA);
		else
			scene.background = background;
	});
	document.body.appendChild(modes);

	window.addEventListener('resize', () => {
		camera.aspect = window.innerWidth / window.innerHeight;
		camera.updateProjectionMatrix();
		stereofx.setSize(window.innerWidth, window.innerHeight);
		controls.handleResize();
	});

	document.body.appendChild(renderer.domElement);
	controls.handleResize();

	if (document.location.hash)
		parseLogFetch(document.location.hash.substr(1));
	window.addEventListener("hashchange", e => {
		parseLogFetch(document.location.hash.substr(1));
	});

	document.ondragover = () => false;
	document.ondragenter = () => false;
	document.ondrop = e => {
		e = e || window.event;
		e.preventDefault();
		const file = (e.files || e.dataTransfer.files)[0];
		const reader = new FileReader();
		reader.onload = ev => {
			const data = ev.target.result;
			parseLog(data);
		}
		reader.readAsArrayBuffer(file);
		return false;
	};

	render(0);
}

function render(time) {
	requestAnimationFrame(render);
	controls.update();
	camera.up.set(0, 1, 0);
	if (path_line) path_line.material.uniforms.t.value = time;
	stereofx.render(scene, camera);
}
