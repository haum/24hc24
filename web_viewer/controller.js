import * as THREE from 'three';
import { TrackballControls } from 'three/addons/controls/TrackballControls.js';

export class ViewerControls {
	constructor(camera, obj, dom) {
		this.cam = camera;
		this.obj = obj;
		this.dom = dom;

		this.trackball = new TrackballControls(camera, dom);
		this.trackball.target = obj.position.clone();
		this.trackball.rotateSpeed = 1.0;
		this.trackball.zoomSpeed = 1.0;
		this.trackball.panSpeed = 0.1;
		this.trackball.keys = ['CtrlLeft', 'AltLeft', 'ShiftLeft'];
	}

	handleResize() {
		this.trackball.handleResize();
	}

	update(time) {
		this.trackball.update();
		this.cam.up.set(0, 1, 0);
	}
};
