Title: A real Hello World example for react
Date: 2017-01-21
Tags: react, helloworld, example

I got frustrated following the React
["Hello, World"](https://facebook.github.io/react/docs/hello-world.html) and 
[tutorial](https://facebook.github.io/react/tutorial/tutorial.html)
because of the implied magic. How does it actually work? Where does it fit
into a html page? _How do I run React locally?_

The "Hello, World" has a 4 line example that does not actually work: _this_ is
the minimal react "Hello, World". If you save this to a file (e.g.
`hello_world.html`), you will be able to open it with your favorite web
browser:

```
:::html
<!DOCTYPE html>
<html>
		<head>
				<meta charset="UTF-8" />
				<script src="https://unpkg.com/react@latest/dist/react.js"></script>
				<script src="https://unpkg.com/react-dom@latest/dist/react-dom.js"></script>
				<script src="https://unpkg.com/babel-standalone@latest/babel.min.js"></script>
				<script type="text/babel">
						ReactDOM.render(
								<h1>Hello, World!</h1>,
								document.getElementById('root')
						);
				</script>
		</head>
		<body>
				<div id="root"/>
		</body>
</html>
```

