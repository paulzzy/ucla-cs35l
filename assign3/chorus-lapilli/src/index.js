import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";

function Square(props) {
	return (
		<button
			className="square"
			onClick={props.onClick}
			style={{ backgroundColor: props.bgColor }}
		>
			{props.value}
		</button>
	);
}

class Board extends React.Component {
	renderSquare(i) {
		return (
			<Square
				value={this.props.squares[i]}
				onClick={() => this.props.onClick(i)}
				bgColor={this.props.bgColor(i)}
			/>
		);
	}

	render() {
		return (
			<div>
				<div className="board-row">
					{this.renderSquare(0)}
					{this.renderSquare(1)}
					{this.renderSquare(2)}
				</div>
				<div className="board-row">
					{this.renderSquare(3)}
					{this.renderSquare(4)}
					{this.renderSquare(5)}
				</div>
				<div className="board-row">
					{this.renderSquare(6)}
					{this.renderSquare(7)}
					{this.renderSquare(8)}
				</div>
			</div>
		);
	}
}

class Game extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			history: [
				{
					squares: Array(9).fill(null),
				},
			],
			stepNumber: 0,
			xIsNext: true,
			selectedPiece: -1,
			invalidMove: false,
		};
	}

	adjacent(pieceIndex) {
		if (this.state.selectedPiece === -1) {
			return false;
		}

		const candidate = { x: pieceIndex % 3, y: Math.floor(pieceIndex / 3) };
		const selected = {
			x: this.state.selectedPiece % 3,
			y: Math.floor(this.state.selectedPiece / 3),
		};

		const x_distance = Math.abs(candidate.x - selected.x);
		const y_distance = Math.abs(candidate.y - selected.y);
		const distance = x_distance + y_distance;

		return distance === 1 || (x_distance === 1 && y_distance === 1);
	}

	handleClick(i) {
		const history = this.state.history.slice(0, this.state.stepNumber + 1);
		const current = history[history.length - 1];
		const squares = current.squares.slice();

		const lapilliMode = this.state.stepNumber > 5; // True when pieces can only be moved
		const hasSelected = this.state.pieceSelected === -1;
		const playerSymbol = this.state.xIsNext ? "X" : "O";

		const centerPiece = 4;
		let invalidMove = false;

		// Disallow board changes after a player wins
		if (calculateWinner(squares)) {
			return;
		}

		let piece = squares[i];
		let select = this.state.selectedPiece;

		if (!lapilliMode && piece === null) {
			// Place on empty square
			squares[i] = playerSymbol;
		} else if (lapilliMode && !hasSelected && squares[i] === playerSymbol) {
			// Select one of current player's pieces
			select = i;
		} else if (lapilliMode && piece === null && this.adjacent(i)) {
			const testSquares = squares.slice();
			testSquares[i] = playerSymbol;
			testSquares[this.state.selectedPiece] = null;

			// If the center square has one of the current player's pieces, they must either win or move their center piece.
			if (
				squares[centerPiece] === playerSymbol &&
				calculateWinner(testSquares) === null &&
				this.state.selectedPiece !== centerPiece
			) {
				invalidMove = true;
			}

			// Move piece to an empty and adjacent square
			squares[i] = playerSymbol;
			squares[this.state.selectedPiece] = null;
			select = -1;
		} else {
			return;
		}

		const updateBoard = select === -1 && !invalidMove;

		this.setState({
			history: updateBoard
				? history.concat([
						{
							squares: squares,
						},
				  ])
				: history,
			stepNumber: updateBoard ? history.length : history.length - 1,
			// Only update when placing or moving
			xIsNext: updateBoard ? !this.state.xIsNext : this.state.xIsNext,
			selectedPiece: select,
			invalidMove: invalidMove,
		});
	}

	jumpTo(step) {
		this.setState({
			stepNumber: step,
			xIsNext: step % 2 === 0,
			selectedPiece: -1,
			invalidMove: false,
		});
	}

	render() {
		const history = this.state.history;
		const current = history[this.state.stepNumber];
		const winner = calculateWinner(current.squares);

		const normalColor = "#ffffff";
		const highlightColor = "#cccccc";

		const moves = history.map((step, move) => {
			const desc = move ? "Go to move #" + move : "Go to game start";
			return (
				<li key={move}>
					<button onClick={() => this.jumpTo(move)}>{desc}</button>
				</li>
			);
		});

		let status;
		if (winner) {
			status = "Winner: " + winner;
		} else {
			status = `Next player: ${this.state.xIsNext ? "X" : "O"}${
				this.state.invalidMove
					? " — Invalid move: Either win or move from center."
					: ""
			}`;
		}

		return (
			<div className="game">
				<div className="game-board">
					<Board
						squares={current.squares}
						onClick={(i) => this.handleClick(i)}
						bgColor={(i) =>
							i === this.state.selectedPiece ? highlightColor : normalColor
						}
					/>
				</div>
				<div className="game-info">
					<div>{status}</div>
					<ol>{moves}</ol>
				</div>
			</div>
		);
	}
}

// ========================================

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<Game />);

function calculateWinner(squares) {
	const lines = [
		[0, 1, 2],
		[3, 4, 5],
		[6, 7, 8],
		[0, 3, 6],
		[1, 4, 7],
		[2, 5, 8],
		[0, 4, 8],
		[2, 4, 6],
	];
	for (let i = 0; i < lines.length; i++) {
		const [a, b, c] = lines[i];
		if (squares[a] && squares[a] === squares[b] && squares[a] === squares[c]) {
			return squares[a];
		}
	}
	return null;
}
