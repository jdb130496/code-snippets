var request = require('request');
var options = {
  'method': 'POST',
  'url': 'https://json.freeastrologyapi.com/complete-panchang',
  'headers': {
    'Content-Type': 'application/json',
    'x-api-key': '3eAV0rBhkM1bZjxTAsEkZ5IfIOXHe5SOiFt2Cm06'
  },
  body: JSON.stringify({
    "year": 2022,
    "month": 8,
    "date": 11,
    "hours": 6,
    "minutes": 0,
    "seconds": 0,
    "latitude": 17.38333,
    "longitude": 78.4666,
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

