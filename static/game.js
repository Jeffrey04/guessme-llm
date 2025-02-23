function initialize() {
	const reset = document.getElementById("reset");

	game_reset();

	reset.addEventListener("click", (event) => {
		event.stopPropagation();
		event.preventDefault();

		const prompt = document.getElementById("prompt");

		prompt.disabled = true;

		game_reset();
	});
}

function game_reset() {
	const socket = new WebSocket("./chat");

	const prompt = document.getElementById("prompt");
	const response = document.getElementById("response");
	const form = document.getElementById("form");
	const history = document.getElementById("history");

	const handle_submit = (event) => {
		event.stopPropagation();
		event.preventDefault();

		socket.send(prompt.value);
		prompt.value = "";
	};
	const handle_close = (event) => {
		form.removeEventListener("submit", handle_submit);
	};

	form.addEventListener("submit", handle_submit);
	socket.addEventListener("message", game_response);
	socket.addEventListener("close", handle_close);

	history.innerHTML = "";
	response.innerHTML = "";
}

function game_response(event) {
	const prompt = document.getElementById("prompt");
	const response = document.getElementById("response");
	const history = document.getElementById("history");
	const template_response = document.getElementById("template-response");
	const template_history = document.getElementById("template-history");
	const data = JSON.parse(event.data);

	console.log(data);
	response.innerHTML = _.template(template_response.innerHTML)({
		data: data.message,
	});

	if (data.type === "question" || data.type === "guess") {
		history.innerHTML = _.template(template_history.innerHTML)({
			type: data.type,
			input: data.input,
			response: data.response,
		}).concat(history.innerHTML);
	}

	prompt.disabled = false;
	prompt.focus();
}

document.addEventListener("DOMContentLoaded", initialize);