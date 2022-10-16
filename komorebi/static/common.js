// Humanise any timestamps
window.addEventListener("DOMContentLoaded", () => {
	let humanise = (dt) => luxon.DateTime.fromISO(dt).toRelative();
	document.querySelectorAll("time").forEach((elem, _) => {
		if (elem.dateTime != "") {
			elem.innerText = humanise(elem.dateTime);
		}
	});
});

// YouTube embed façade
window.addEventListener('DOMContentLoaded', () => {
	document.querySelectorAll("div.facade").forEach((elem, _) => {
		// Because YouTube has stupid black bars above and below each thumbnail
		const ytSux = /\/i\.ytimg\.com\//;
		if ("thumb" in elem.dataset) {
			let thumb = document.createElement("img");
			thumb.alt = "Video: " + elem.title;
			thumb.src = elem.dataset.thumb;
			thumb.width = elem.dataset.width;
			if ("height" in elem.dataset && !ytSux.test(elem.dataset.thumb)) {
				thumb.height = elem.dataset.height;
			}
			thumb.referrerPolicy = "no-referrer";
			thumb.loading = "lazy";
			elem.appendChild(thumb);
		}

		let play = document.createElement("span");
		play.innerText = "▶";
		elem.appendChild(play);

		elem.style.height = elem.dataset.height + "px";
		elem.style.width = elem.dataset.width + "px";

		elem.addEventListener("click", () => {
			let url = new URL(elem.dataset.src);
			// A YouTube-ism that might be supported elsewhere...
			url.searchParams.set('autoplay', '1');

			let iframe = document.createElement('iframe');
			iframe.className = "player";
			iframe.src = url.href;
			iframe.width = elem.dataset.width;
			iframe.height = elem.dataset.height;
			iframe.frameBorder = "0";
			iframe.sandbox = "allow-same-origin allow-scripts";
			iframe.allow = "autoplay; clipboard-write; encrypted-media; picture-in-picture";

			elem.parentNode.replaceChild(iframe, elem);
		}, { "once": true, "capture": true });
	});
});
