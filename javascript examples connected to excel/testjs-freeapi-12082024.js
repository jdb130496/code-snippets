var request = require('request');
var options = {
  'method': 'POST',
  'url': 'https://json.freeastrologyapi.com/lunarmonthinfo',
  'headers': {
    'Content-Type': 'application/json',
    'x-api-key': '3eAV0rBhkM1bZjxTAsEkZ5IfIOXHe5SOiFt2Cm06'
  },
  body: JSON.stringify({
    "year": 2024,
    "month": 8,
    "date": 30,
    "hours": 8,
    "minutes": 0,
    "seconds": 0,
    "latitude": 22.310696,
    "longitude": 73.192635,
    "timezone": 5.5,
    "config": {
      "observation_point": "topocentric",
      "ayanamsha": "lahiri"
    }
  })

};
request(options, function (error, response) {
  if (error) throw new Error(error);
  console.log(response.body);
});
