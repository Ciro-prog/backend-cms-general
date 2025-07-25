// auto_mapper.js

function autoMapFields(apiFields, entityFields) {
    // Mapeo por nombre similar (ignorando mayúsculas, guiones, etc)
    const normalize = s => s.toLowerCase().replace(/[^a-z0-9]/g, '');
    const mapping = {};
    entityFields.forEach(entity => {
        const match = apiFields.find(api => normalize(api.name) === normalize(entity.name));
        if (match) {
            mapping[entity.name] = match.name;
        }
    });
    return mapping;
} 