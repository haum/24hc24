import * as THREE from 'three';
import { StereoscopicEffects } from 'threejs-StereoscopicEffects';
import { ViewerControls } from './controller.js';

let scene, background, lights, camera, renderer, controls, stereofx, modecombo, playbtns;
let CUBESZ = 0.1;
let stereorender = true;
const world = new THREE.Group();
const raycaster = new THREE.Raycaster();
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
let playable_url = null;

const line_material = new THREE.ShaderMaterial({
	uniforms: {
		"t": { value: 0.0 },
		"maxActions": { value: 1.0 }
	},
	linewidth: 3,
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

const titleCanvas = document.createElement('canvas');
function addTitle(text) {
	titleCanvas.height = 64;
	const ctx = titleCanvas.getContext('2d');
	const font = '48px monospace';

	ctx.font = font;
	titleCanvas.width = Math.ceil(ctx.measureText(text).width + 32);

	ctx.font = font;
	ctx.rect(0, 0, titleCanvas.width, titleCanvas.height);
	ctx.fillStyle = '#0066d4';
	ctx.fill();

	ctx.fillStyle = '#fff';
	ctx.fillText(text, 16, 48);

	const texture = new THREE.Texture(ctx.getImageData(0, 0, titleCanvas.width, titleCanvas.height));
	texture.colorSpace = THREE.SRGBColorSpace;
	texture.needsUpdate = true;
	const geometry = new THREE.PlaneGeometry(titleCanvas.width/2000, titleCanvas.height/2000);
	const material = new THREE.MeshBasicMaterial( { map: texture } );
	const mesh = new THREE.Mesh(geometry, material);

	mesh.minFilter = THREE.LinearFilter;
	mesh.generateMipmaps = false;
	mesh.needsUpdate = true;

	const cc = coord_xyz_w(0, 0, 0)
	mesh.position.set(
		cc.wx - CUBESZ/2 + geometry.parameters.width/2,
		cc.wy - CUBESZ/2 - geometry.parameters.height/2,
		cc.wz - CUBESZ/2
	);
	world.add(mesh);
}

function addCube(i, t, px, py, pz, mx, my, mz) {
	const p = coord_l2xyz(i);
	const sx = (px+mx)*CUBESZ/6;
	const sy = (py+my)*CUBESZ/6;
	const sz = (pz+mz)*CUBESZ/6;
	const geometry = new THREE.BoxGeometry(sx, sy, sz);
	const cube = new THREE.Mesh(geometry, cube_types[t]);
	cube.position.x = p.wx + (sx - mx/3 * CUBESZ)/2;
	cube.position.y = p.wy + (sy - my/3 * CUBESZ)/2;
	cube.position.z = p.wz + (sz - mz/3 * CUBESZ)/2;
	cube.renderOrder = 1;
	cube.animation = animations[2*t];
	world.add(cube);

	const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geometry), line_types[t]);
	edges.computeLineDistances();
	edges.position.add(cube.position);
	edges.animation = animations[2*t+1];
	world.add(edges);
}

const path_sphere_material = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.5 });
const path_sphere_material_ko = new THREE.MeshBasicMaterial({ color: 0xaa0000, transparent: true, opacity: 0.5 });
const path_sphere_material_ok = new THREE.MeshBasicMaterial({ color: 0x00aa00, transparent: true, opacity: 0.5 });
const path_spheres = [];
const pathdata = {
	'px': 0, 'py': 0, 'pz': 0,
	'vx': 0, 'vy': 0, 'vz': 0,
	'moves': 0
};
function path_rebuild_line() {
	if (path_line) world.remove(path_line);
	const pts = []
	const actions = []
	for (let p of path_spheres) {
		pts.push(p.position);
		actions.push(actions.length);
	}
	actions[actions.length-1] = pathdata.moves;
	const geometry = new THREE.BufferGeometry().setFromPoints(pts);
	geometry.setAttribute('actionNb', new THREE.Float32BufferAttribute(actions, 1));
	path_line = new THREE.Line(geometry, line_material);
	path_line.computeLineDistances();
	path_line.material.uniforms.maxActions.value = actions[actions.length-1];
	world.add(path_line);
}
function addPath_line_START(px, py, pz) {
	pathdata.px = px;
	pathdata.py = py;
	pathdata.pz = pz;
	pathdata.vx = pathdata.vy = pathdata.vz = pathdata.moves = 0;

	const sphere_geometry = new THREE.SphereGeometry(CUBESZ/20, 8, 8);
	const sphere = new THREE.Mesh(sphere_geometry, path_sphere_material);
	const q = coord_xyz_w(px, py, pz);
	sphere.position.set(q.wx, q.wy, q.wz);
	world.add(sphere);

	for (let s of path_spheres) world.remove(s);
	path_spheres.splice(0, path_spheres.length);
	path_spheres.push(sphere);

	if (playable_url) {
		if (playbtns) world.remove(playbtns);
		playbtns = new THREE.Group()
		const playbtn_material = new THREE.MeshBasicMaterial({ color: 0xaa00ff, transparent: true, opacity: 0.5 });
		const playbtn_geometry = new THREE.BoxGeometry(CUBESZ/10, CUBESZ/10, CUBESZ/10);
		for (let i of [-1, 0, 1]) for (let j of [-1, 0, 1]) for (let k of [-1, 0, 1]) {
			const playbtn = new THREE.Mesh(playbtn_geometry, playbtn_material);
			playbtn.position.set(i * CUBESZ, j * CUBESZ, k * CUBESZ);
			playbtn.userData.onclick = () => {
				if (!playbtns.visible) return;
				playbtns.visible = false;
				play(i, j, k).then(() => { if (playable_url) playbtns.visible = true; });
			};
			playbtns.add(playbtn);
		}
		world.add(playbtns);

		playbtns.position.add(sphere.position);
		playbtns.visible = !stereorender;
	}
}
function addPath_line_ACC(ax, ay, az) {
	pathdata.vx += ax;
	pathdata.vy += ay;
	pathdata.vz += az;
	pathdata.px += pathdata.vx;
	pathdata.py += pathdata.vy;
	pathdata.pz += pathdata.vz;
	pathdata.moves += 1;

	const sphere_geometry = new THREE.SphereGeometry(CUBESZ/20, 8, 8);
	const sphere = new THREE.Mesh(sphere_geometry, path_sphere_material);
	const q = coord_xyz_w(pathdata.px, pathdata.py, pathdata.pz);
	sphere.position.set(q.wx, q.wy, q.wz);
	world.add(sphere);
	path_spheres.push(sphere);

	const qb = coord_xyz_w(pathdata.px + pathdata.vx, pathdata.py + pathdata.vy, pathdata.pz + pathdata.vz);
	playbtns.position.set(qb.wx, qb.wy, qb.wz);
}
function addPath_line_END(ok, moves) {
	const last_i = Math.floor(moves) + 1;
	const nextra = path_spheres.length - last_i;
	if (nextra > 0) {
		for (let i = last_i+1; i < path_spheres.length; i++) {
			world.remove(path_spheres[i]);
		}
		path_spheres.splice(last_i + 1, nextra);
	}
	if (last_i < path_spheres.length && last_i > 0) {
		const dv = new THREE.Vector3();
		dv.subVectors(path_spheres[last_i-1].position, path_spheres[last_i].position);
		dv.multiplyScalar(1 - (moves % 1));
		path_spheres[last_i].position.add(dv);
		path_spheres[last_i].material = ok ? path_sphere_material_ok : path_sphere_material_ko;
	}
	pathdata.moves = moves;
	playable_url = null;
	playbtns.visible = false;
}
function addPath_lines(txt) {
	const lines = txt.match(/.*\n/g) || [];
	for (const line of lines) {
		const d = line.split(/\s/);
		if (d[0] == "START") {
			const px = parseInt(d[1]);
			const py = parseInt(d[2]);
			const pz = parseInt(d[3]);
			addPath_line_START(px, py, pz)
		} else if (d[0] == "ACC") {
			const ax = parseInt(d[1]);
			const ay = parseInt(d[2]);
			const az = parseInt(d[3]);
			addPath_line_ACC(ax, ay, az);
		} else if (d[0] == "END") {
			const ok = d[1] == "OK";
			const moves = parseFloat(d[2]);
			addPath_line_END(ok, moves);
		}
	}
	path_rebuild_line();
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
		const map = txt.match(/MAP[^\n]+\n/)?.[0]?.split(/\s+/);
		if (!map) return;
		gridSize = { x: parseInt(map[1]), y: parseInt(map[2]), z: parseInt(map[3]) };
		CUBESZ = 1 / Math.max(gridSize.x, gridSize.y, gridSize.z);
	}

	// Playable
	{
		const playable = txt.match(/PLAYABLE ([^\n]+)\n/);
		playable_url = playable ? playable[1] : null;
	}

	// Grid on
	{
		const gridon = txt.match(/GRID ON\n/);
		addGrid(gridon != null);
	}

	// Title
	{
		const title = txt.match(/TITLE ([^\n]+)\n/);
		if (title) addTitle(title[1]);
	}

	// Auto load
	{
		const autoload = txt.match(/AUTOLOAD (\d+) ([^\n]+)\n/);
		if (autoload) {
			const duration = Math.max(1, parseInt(autoload[1])) * 1000;
			setTimeout(() => {
				document.location.hash = autoload[2];
			}, duration);
		}
	}

	// Decode grid
	{
		const grid = txt.match(/MAP.*\n([\s\S]*)ENDMAP/m)[1]?.replaceAll(/[^A-Za-z0-9+\/]+/g, '')?.match(/.{3}/g) || [];
		for (const [i, v] of grid.entries()) {
			if (v == 'AAA') continue;
			const nb = b64_atoi(v);
			const px = (nb & (3 << 0)) >> 0;
			const mx = (nb & (3 << 2)) >> 2;
			const py = (nb & (3 << 4)) >> 4;
			const my = (nb & (3 << 6)) >> 6;
			const pz = (nb & (3 << 8)) >> 8;
			const mz = (nb & (3 << 10)) >> 10;
			const bt = (nb & (7 << 12)) >> 12;
			addCube(i, bt, px, py, pz, mx, my, mz);
		}
	}

	// Path
	{
		const path = txt.match(/(START[\s\S]*END.*\n)/m)?.[1] || txt.match(/(START[\s\S]*\n)/)?.[1];
		if (path) addPath_lines(path);
	}
}

export function parseLogFetch(url) {
	fetch(url)
		.then(r => r.arrayBuffer())
		.then(b => parseLog(b));
}

async function play(Ax, Ay, Az) {
	if (!playable_url) return;
	const r = await fetch(playable_url, { method: "POST", headers: { "Content-Type": "text/plain" }, body: "ACC " + Ax + " " + Ay + " " + Az });
	const t = await r.text();
	addPath_lines(t);
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

function changeStereoMode(mode) {
	stereofx.setEffect(mode);
	if (mode > 18)
		scene.background = new THREE.Color(0xAAAAAA);
	else
		scene.background = background;
	stereorender = (mode != 'm');
	if (playbtns) playbtns.visible = playable_url && !stereorender;
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

	const overlay = document.createElement('div');
	document.body.appendChild(overlay);

	modecombo = StereoscopicEffects.effectsListForm();
	modecombo.firstChild.label = "Monoscopic"
	modecombo.firstChild.firstChild.remove();
	modecombo.firstChild.firstChild.label = "Monoscopic";
	modecombo.firstChild.firstChild.value = "m";
	modecombo.value = defaultEffect;
	modecombo.style.position = 'absolute';
	modecombo.style.top = 0;
	modecombo.style.right = 0;
	modecombo.addEventListener('change', () => changeStereoMode(modecombo.value));
	changeStereoMode(defaultEffect);
	overlay.appendChild(modecombo);
	document.addEventListener('keydown', e => {
		if (e.keyCode == 77)
			overlay.style.display = (overlay.style.display == 'none') ? 'block' : 'none';
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
		overlay.appendChild(btn_vr);
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
		overlay.appendChild(btn_ar);
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

	renderer.domElement.addEventListener('click', e => {
		if (stereorender) return;
		const raycast_pointer = new THREE.Vector2();
		raycast_pointer.x = (e.clientX / window.innerWidth) * 2 - 1;
		raycast_pointer.y = -(e.clientY / window.innerHeight) * 2 + 1;
		raycaster.setFromCamera(raycast_pointer, camera);

		const intersects = raycaster.intersectObjects(playbtns.children, false);
		for (let it of intersects) {
			if ('onclick' in it.object.userData) {
				it.object.userData.onclick(it);
				break;
			}
		}
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
	if (stereorender)
		stereofx.render(scene, camera);
	else
		renderer.render(scene, camera);
}
