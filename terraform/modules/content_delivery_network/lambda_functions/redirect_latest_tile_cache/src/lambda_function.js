const aws = require('aws-sdk');
const s3 = new aws.S3({region: 'us-east-1'});

let bucket = {
    "production": "gfw-tiles",
    "staging": "gfw-tiles-staging",
    "dev": "gfw-tiles-dev",
    "test": "gfw-tiles-test"
};

const TTL = 5000; // TTL of 5 seconds

async function fetchRedirectionsFromS3(env) {

    const s3Params = {
        Bucket: bucket[env],
        Key: 'latest',
    };

    console.log("Bucket: " + s3Params.Bucket);
    console.log("Key: " + s3Params.Key);

    const response = await s3.getObject(s3Params).promise();
    return JSON.parse(response.Body.toString('utf-8')).map(
        ({name, latest_version}) => ({
            name: new RegExp(name),
            latest_version,
        })
    );
}

let redirections;

function fetchRedirections(env) {
    if (!redirections) {
        redirections = fetchRedirectionsFromS3(env);

        setTimeout(() => {
            redirections = undefined;
        }, TTL);
    }

    return redirections;
}

exports.handler = async event => {
    var request = event.Records[0].cf.request;
    const customHeaders = request.origin.s3.customHeaders;
    const env = customHeaders["x-env"][0].value;
    console.log("REQUEST URI:" + request.uri);
    var elements = request.uri.split('/');
    const dataset = elements[1];
    console.log("DATASET: " + dataset);

    try {
        const redirects = await fetchRedirections(env);

        for (const {name, latest_version} of redirects) {
            if (name.test(dataset)) {

                console.log("LATEST VERSION: " + latest_version);
                elements.forEach((element, index) => {
                    if (element === "latest") {
                        elements[index] = latest_version;
                    } else {
                        elements[index] = element
                    }
                });

                request.uri = elements.join('/');

                return request;
            }
        }

        return request;

    } catch (_error) {
        console.log("ERROR: " + _error);
        return request;
    }
};
