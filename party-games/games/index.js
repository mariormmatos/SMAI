// Game registry
const quiz = require('./quiz');
const bluff = require('./bluff');
const creative = require('./creative');
const mission = require('./mission');
const consensus = require('./consensus');

const registry = { quiz, bluff, creative, mission, consensus };

module.exports = {
  getGame(name) {
    return registry[name] || null;
  },
};
