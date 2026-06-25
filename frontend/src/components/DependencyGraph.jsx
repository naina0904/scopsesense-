import React from "react";

import ReactFlow, {

    Background,
    Controls

} from "reactflow";

import "reactflow/dist/style.css";


function DependencyGraph({

    dependencies = []
}) {

    // -----------------------------------
    // CREATE NODES + EDGES
    // -----------------------------------

    const nodes = [];

    const edges = [];

    const createdNodes = new Set();

    let yPosition = 0;

    dependencies.forEach(

        (item, index) => {

            const sourceId =
                item.file;

            // -----------------------------------
            // SOURCE NODE
            // -----------------------------------

            if (
                !createdNodes.has(
                    sourceId
                )
            ) {

                nodes.push({

                    id: sourceId,

                    data: {
                        label: sourceId
                    },

                    position: {

                        x: 100,

                        y: yPosition
                    },

                    style: {

                        padding: 12,

                        borderRadius: 12,

                        border:
                            "1px solid #334155",

                        background:
                            "#0f172a",

                        color: "#fff",

                        width: 220
                    }
                });

                createdNodes.add(
                    sourceId
                );

                yPosition += 150;
            }

            // -----------------------------------
            // IMPORTS
            // -----------------------------------

            item.imports.forEach(

                (
                    dependency,
                    depIndex
                ) => {

                    const targetId =
                        dependency;

                    if (
                        !createdNodes.has(
                            targetId
                        )
                    ) {

                        nodes.push({

                            id: targetId,

                            data: {
                                label: targetId
                            },

                            position: {

                                x: 500,

                                y:
                                    index * 200
                                    + depIndex * 100
                            },

                            style: {

                                padding: 12,

                                borderRadius: 12,

                                border:
                                    "1px solid #334155",

                                background:
                                    "#1e293b",

                                color: "#fff",

                                width: 220
                            }
                        });

                        createdNodes.add(
                            targetId
                        );
                    }

                    edges.push({

                        id:
                            `${sourceId}-${targetId}`,

                        source:
                            sourceId,

                        target:
                            targetId,

                        animated: true
                    });
                }
            );
        }
    );

    return (

        <div
            className="
            h-[700px]
            rounded-2xl
            overflow-hidden
            border
            border-slate-800
        "
        >

            <ReactFlow

                nodes={nodes}

                edges={edges}

                fitView

            >

                <Background />

                <Controls />

            </ReactFlow>

        </div>
    );
}

export default DependencyGraph;