exports.handler = async (event, context) => {

    function has(object, key) {
      return object ? hasOwnProperty.call(object, key) : false;
   }

    const response = event.Records[0].cf.response;
    const headers = response.headers;

    if (typeof(headers.expires) !== 'undefined') {delete headers.expires;}

    headers['cache-control'] = [{
        key:   'Cache-Control',
        value: "max-age=21600"
    }];

    console.log("Overwrite headers for " + response.uri);
    return response;
};
