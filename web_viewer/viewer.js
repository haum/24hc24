import * as THREE from 'three';
import { StereoscopicEffects } from 'threejs-StereoscopicEffects';
import { ViewerControls } from './controller.js';

let scene, background, lights, camera, renderer, controls, stereofx, modecombo;
const CUBESZ = 0.1;
const world = new THREE.Group();
const cube_types = [
	new THREE.MeshLambertMaterial({ color: 0x333333, transparent: true, opacity: 0.8 }), // Goals
	new THREE.MeshLambertMaterial({ color: 0x0066d4, transparent: true, opacity: 0.8 }), // Asteroids
	new THREE.MeshLambertMaterial({ color: 0xffcc00, transparent: true, opacity: 0.2 }), // Nebulae
	new THREE.MeshLambertMaterial({ color: 0xcccccc, transparent: true, opacity: 0.2 }), // Magnetic clouds
	new THREE.MeshLambertMaterial({ color: 0x677821, transparent: true, opacity: 0.1 }), // Checkpoint 1
	new THREE.MeshLambertMaterial({ color: 0x677821, transparent: true, opacity: 0.1 }), // Checkpoint 2
	new THREE.MeshLambertMaterial({ color: 0x677821, transparent: true, opacity: 0.1 }), // Checkpoint 3
	new THREE.MeshLambertMaterial({ color: 0x677821, transparent: true, opacity: 0.1 }), // Checkpoint 4
];
const line_types = [
	new THREE.LineBasicMaterial({ color: cube_types[0].color }),
	new THREE.LineBasicMaterial({ color: cube_types[1].color, transparent: true }),
	new THREE.LineBasicMaterial({ color: cube_types[2].color }),
	new THREE.LineBasicMaterial({ color: cube_types[3].color }),
	new THREE.LineDashedMaterial({ color: cube_types[4].color, dashSize: CUBESZ/50, gapSize: CUBESZ/50 }),
	new THREE.LineDashedMaterial({ color: cube_types[5].color, dashSize: CUBESZ/50, gapSize: CUBESZ/50 }),
	new THREE.LineDashedMaterial({ color: cube_types[6].color, dashSize: CUBESZ/50, gapSize: CUBESZ/50 }),
	new THREE.LineDashedMaterial({ color: cube_types[7].color, dashSize: CUBESZ/50, gapSize: CUBESZ/50 })
];
const animations = [
	null, null,
	animWall(0.1, 0.8, 3), animWall(0, 1, 3),
	null, null,
	null, null,
	animCheckpoint(1, 5, 0.1, 0.4), null,
	animCheckpoint(2, 5, 0.1, 0.4), null,
	animCheckpoint(3, 5, 0.1, 0.4), null,
	animCheckpoint(4, 5, 0.1, 0.4), null,
];

let gridSize = { x: 10, y: 10, z: 10 };
let path_line = null;

function coord_xyz_w(x, y, z) {
	return {
		x: x, y: y, z: z,
		wx: (x - (gridSize.x - 1)/2) * CUBESZ,
		wy: (y - (gridSize.y - 1)/2) * CUBESZ,
		wz: (z - (gridSize.z - 1)/2) * CUBESZ,
	};
}

function coord_l2xyz(i) {
	const z = Math.floor(i / (gridSize.x * gridSize.y));
	i -= z * gridSize.x * gridSize.y;
	const y = Math.floor(i / gridSize.x);
	const x = i % gridSize.x;
	return coord_xyz_w(x, y, z);
}

function coord_xyz2l(x, y, z) {
	return x + y * gridSize.x + z * gridSize.x * gridSize.y;
}

function rmDynobjs() {
	const children = [...world.children];
	for (const obj of children) {
		world.remove(obj);
	}
}

function addGrid(inside) {
	if (inside) {
		const n = gridSize.x * gridSize.y * gridSize.z;
		const vertices = [];
		for (let i = 0; i < n; i++) {
			const p = coord_l2xyz(i);
			vertices.push(p.wx, p.wy, p.wz);
		}
		const geometry = new THREE.BufferGeometry();
		geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
		const material = new THREE.PointsMaterial({ color: 0xffffff, size: CUBESZ/10 });
		const points = new THREE.Points(geometry, material);
		world.add(points);
	}

	{
		const geometry = new THREE.BoxGeometry(gridSize.x*CUBESZ, gridSize.y*CUBESZ, gridSize.z*CUBESZ);
		const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geometry), new THREE.LineBasicMaterial({color: cube_types[1].color}));
		world.add(edges);
	}
}

function addCube(i, t, px, py, pz, mx, my, mz) {
	const p = coord_l2xyz(i);
	const sx = (px+mx)*CUBESZ/2;
	const sy = (py+my)*CUBESZ/2;
	const sz = (pz+mz)*CUBESZ/2;
	const geometry = new THREE.BoxGeometry(sx, sy, sz);
	const cube = new THREE.Mesh(geometry, cube_types[t]);
	cube.position.x = p.wx + (sx - mx * CUBESZ)/2;
	cube.position.y = p.wy + (sy - my * CUBESZ)/2;
	cube.position.z = p.wz + (sz - mz * CUBESZ)/2;
	cube.renderOrder = 1;
	cube.animation = animations[2*t];
	world.add(cube);

	const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geometry), line_types[t]);
	edges.computeLineDistances();
	edges.position.add(cube.position);
	edges.animation = animations[2*t+1];
	world.add(edges);
}

function addPath(pts, actions) {
	const sphere_geometry = new THREE.SphereGeometry(CUBESZ/20, 8, 8);
	const sphere_material = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.5 });
	for (const pt of pts.slice(0, -1)) {
		const sphere = new THREE.Mesh(sphere_geometry, sphere_material);
		sphere.position.add(pt);
		world.add(sphere);
	}
	if (pts.length == 1) {
		const sphere = new THREE.Mesh(sphere_geometry, sphere_material);
		sphere.position.add(pts[0]);
		world.add(sphere);
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
	path_line = line;
	world.add(line);
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
		const path = (txt.match(/(START[\s\S]*END.*\n)/m)?.[1] || txt.match(/(START[\s\S]*\n)/)?.[1])?.match(/.*\n/g) || [];
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
				const q = coord_xyz_w(px, py, pz);
				points.push(new THREE.Vector3(q.wx, q.wy, q.wz));
				actions.push(0.0);
			} else if (d[0] == "ACC") {
				vx += parseInt(d[1]);
				vy += parseInt(d[2]);
				vz += parseInt(d[3]);
				px += vx;
				py += vy;
				pz += vz;
				const q = coord_xyz_w(px, py, pz);
				points.push(new THREE.Vector3(q.wx, q.wy, q.wz));
				actions.push(actions.length * 1.0);
			} else if (d[0] == "END") {
				const l = Math.min(parseFloat(d[2]), points.length-1);
				const origin = points[Math.floor(l)];
				const destination = points[Math.ceil(l)];
				const ndest = origin.clone().lerp(destination, l%1);
				points.splice(Math.ceil(l));
				points.push(ndest);
				actions.splice(Math.ceil(l));
				actions.push(l);
			}
		}
		addPath(points, actions);
	}
}

export function parseLogFetch(url) {
	fetch(url)
		.then(r => r.arrayBuffer())
		.then(b => parseLog(b));
}

function animWall(opacityMin, opacityMax, duration) {
	return (obj, t) => {
		let tt = (t % (1000*duration))/(1000*duration);
		if (tt > 0.5) tt = 1 - tt;
		tt *= 2;
		obj.material.opacity = opacityMin + tt * (opacityMax - opacityMin);
	}
}

function animCheckpoint(nr, duration) {
	return (obj, t) => {
		let tt = (t % (1000*duration))/(1000*duration);
		const step = Math.round(tt/0.2);
		if (step == nr) obj.material.opacity = 0.8;
		else obj.material.opacity = 0.1;
	}
}

function changeStereomMode(mode) {
	stereofx.setEffect(mode);
	if (mode > 18)
		scene.background = new THREE.Color(0xAAAAAA);
	else
		scene.background = background;
	window.localStorage.setItem("stereoMode", mode);
}

export function init() {
	const defaultEffect = window.localStorage.getItem("stereoMode") || 20;

	scene = new THREE.Scene();
	scene.add(world);
	world.position.set(0, 0, -1);

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

	camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 1/100, 100);
	camera.position.set(0, 0, 0);
	camera.lookAt(world.position);

	renderer = new THREE.WebGLRenderer({ antialias: true });
	renderer.setPixelRatio(window.devicePixelRatio);
	renderer.xr.enabled = true;
	renderer.xr.setReferenceSpaceType('local');
	renderer.xr.setFramebufferScaleFactor(2);
	stereofx = new StereoscopicEffects(renderer);
	stereofx.setSize(window.innerWidth, window.innerHeight);
 
	controls = new ViewerControls(camera, world, renderer.domElement);

	modecombo = StereoscopicEffects.effectsListForm();
	modecombo.value = defaultEffect;
	modecombo.style.position = 'absolute';
	modecombo.style.top = 0;
	modecombo.style.right = 0;
	modecombo.addEventListener('change', () => changeStereomMode(modecombo.value));
	changeStereomMode(defaultEffect);
	document.body.appendChild(modecombo);
	document.addEventListener('keydown', e => {
		if (e.keyCode == 77)
			modecombo.style.display	= (modecombo.style.display == 'none') ? 'block' : 'none';
	});

	const btn_vr = document.createElement('button');
	if ('xr' in navigator) navigator.xr.isSessionSupported('immersive-vr').then((supported) => {
		if (!supported) return;
		btn_vr.innerText = "VR"
		btn_vr.style.width = '100px';
		btn_vr.style.height = '40px';
		btn_vr.style.position = 'absolute';
		btn_vr.style.top = 0;
		btn_vr.style.left = 0;
		btn_vr.addEventListener('click', (e) => {
			e.stopPropagation();
			if (!renderer.xr.isPresenting) {
				navigator.xr.requestSession('immersive-vr').then((s) => {
					renderer.xr.setSession(s);
				});
			} else {
				renderer.xr.getSession()?.end();
			}
		});
		document.body.appendChild(btn_vr);
	});

	const btn_ar = document.createElement('button');
	if ('xr' in navigator) navigator.xr.isSessionSupported('immersive-ar').then((supported) => {
		if (!supported) return;
		btn_ar.innerText = "AR"
		btn_ar.style.width = '100px';
		btn_ar.style.height = '40px';
		btn_ar.style.position = 'absolute';
		btn_ar.style.top = '40px';
		btn_ar.style.left = 0;
		btn_ar.addEventListener('click', (e) => {
			e.stopPropagation();
			if (!renderer.xr.isPresenting) {
				navigator.xr.requestSession('immersive-ar').then((s) => {
					renderer.xr.setSession(s);
				});
			} else {
				renderer.xr.getSession()?.end();
			}
		});
		document.body.appendChild(btn_ar);
	});

	let xr_prev_bg;
	renderer.xr.addEventListener('sessionstart', () => {
		xr_prev_bg = scene.background;
		scene.background = new THREE.Color(0);
		btn_vr.innerText = 'Stop';
		btn_ar.innerText = 'Stop';
	});
	renderer.xr.addEventListener('sessionend', () => {
		scene.background = xr_prev_bg;
		btn_vr.innerText = 'VR';
		btn_ar.innerText = 'AR';
	});

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

	renderer.setAnimationLoop(render);
}

function render(time) {
	controls.update(time);
	for (const o of world.children) if (o.animation) o.animation(o, time);
	if (path_line) path_line.material.uniforms.t.value = time;
	stereofx.render(scene, camera);
}
