async function fetchAndApplyStyles(url) {
  try {
    const response = await fetch(url);
    const styles = await response.json();

    for (const divId in styles) {
      const div = document.getElementById(divId);
      if (div) {
        const styleProps = styles[divId];
        for (const prop in styleProps) {
          div.style[prop] = styleProps[prop];
          // console.log(`Applying ${prop}: ${styleProps[prop]} to`, div);
        }
      }
    }
  } catch (error) {
    console.error('Error fetching styles:', error);
  }
}
