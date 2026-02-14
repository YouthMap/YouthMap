// Loads an image from the provided URL, and gets the colour of the top-left pixel. This is done asynchronously just
// in case loading the image and processing it takes a while for some reason, but in practice it has proven to be quick.
// As an implementation detail, if the top-left pixel is fully transparent, a random colour is generated rather than
// simply defaulting to white or black.
async function getTopLeftPixelColor(imageUrl) {
    try {
        // Load the image
        const img = new Image();
        await new Promise((resolve, reject) => {
            img.onload = resolve;
            img.onerror = reject;
            img.src = imageUrl;
        });

        // Create a canvas and draw the image
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);

        // Extract the colour of the top-left pixel
        var [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data;

        // Fully transparent -> generate random colour
        if (a == 0) {
            r = Math.floor(Math.random() * 256);
            g = Math.floor(Math.random() * 256);
            b = Math.floor(Math.random() * 256);
        }

        // Format the real colour as hex and return it
        return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
    } catch (error) {
    console.log(error);
        return "#000000";
    }
}