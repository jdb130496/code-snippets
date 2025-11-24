const axios = require('axios');

const options = {
  method: 'POST',
  url: 'https://json.freeastrologyapi.com/complete-panchang',
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': '3eAV0rBhkM1bZjxTAsEkZ5IfIOXHe5SOiFt2Cm06'
  },
  data: {
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
  }
};

axios(options)
  .then(response => {
    console.log(response.status);
    console.log(response.headers);
    console.log(response.data);
  })
  .catch(error => {
    console.error(error);
  });

